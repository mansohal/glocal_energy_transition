#
# GAMS - General Algebraic Modeling System Python API
#
# Copyright (c) 2017-2024 GAMS Development Corp. <support@gams.com>
# Copyright (c) 2017-2024 GAMS Software GmbH <support@gams.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from abc import ABC, abstractmethod
import importlib.resources
import yaml
from gams.connect.connectvalidator import ConnectValidator
from gams.connect.errors import GamsConnectException
import pandas as pd
import gams.transfer as gt
from gams.transfer._internals import generate_unique_labels


class ConnectAgent(ABC):
    """
    An abstract base class that defines the structure for Connect agent implementations.

    Subclasses must implement the abstract methods to define their own behavior.
    This class provides a common interface and some shared functionality.

    Parameters
    ----------
    cdb : gams.connect.connectdatabase.ConnectDatabase.
        The Connect Database responsible for the Connect agent.
    inst : dict
        A nested data structure consisting of dictionaries and lists containing the instructions to be executed by the Connect agent.

    Abstract methods:
    - __init__: Connect agent constructor.
    - execute: Called by the ConnectDatabase after open() and before close().

    Class methods:
    - cerberus: Returns the cerberus schema as Python data structure.

    Non-abstract methods:
    - close: Called by the ConnectDatabase after execute().
    - open: Called by the ConnectDatabase before execute().
    - _apply_value_substitutions: Substitutes values in the last column of df as provided in value_subs and returns the modified DataFrame.
    - _connect_error: Raises a GamsConnectException.
    - _describe_container: Logs the status of a gams.transfer.Container.
    - _dict_get: Like dict.get() but handles keys with None value as if they were missing.
    - _log_instructions: Logs raw and processed instructions in a table format.
    - _normalize_instructions: Performs normalization of the given instructions.
    - _pandas_version_before: Checks if the installed pandas version is before the given version string x.y.
    - _sym_records_no_none: Returns the records of a symbol or an empty DataFrame with appropriate column names for None records.
    - _transform_sym_none_to_empty: Sets the records of a symbol to an empty DataFrame with appropriate column names if the given records are None.
    - _update_sym_inst: Updates None values in the symbols scope instructions with the corresponding values from the root scope for all keys that exist in both instruction dictionaries.
    - _check_symbol_exists: Raises a GamsConnectException if a single symbol or at least one symbol of a given list of symbols does exist in the Connect Database.
    - _log_instructions_r: Recursive helper method for instruction logging.
    - _replace_no_warn: Helper method for _apply_value_substitutions().
    """

    @abstractmethod
    def __init__(self, cdb, inst):
        self._col_widths = [30, 30, 30]
        self._no_option_list = [
            "connection",
            "connectionArguments",
            "dimensionMap",
            "dTypeMap",
            "indexSubstitutions",
            "readCSVArguments",
            "readSQLArguments",
            "toCSVArguments",
            "toSQLArguments",
            "valueSubstitutions",
        ]
        self._system_directory = cdb.system_directory
        self._cdb = cdb
        self._inst = inst
        self._trace = 0

    @classmethod
    def cerberus(cls):
        """
        Class method that returns the cerberus schema as Python data structure.

        Returns
        -------
        dict
            Python data structure to be used for validation to ensure correct format of instructions given to a Connect agent.
        """
        with importlib.resources.as_file(importlib.resources.files("gams.connect.agents") / "schema") as schema_path:
            schema_file = schema_path / (cls.__name__ + ".yaml")
            schema = schema_file.read_text()
        return yaml.safe_load(schema)

    def _normalize_instructions(self, inst):
        """
        Performs normalization of the given instructions.

        Parameters
        ----------
        inst : dict
            The instructions to be normalized.

        Returns
        -------
        dict
            The normalized instructions.
        """
        v = ConnectValidator(self.cerberus())
        inst = v.normalized(inst)
        inst = v.normalize_of_rules(inst)
        return inst

    def _log_instructions_r(
        self, inst, has_inst_raw, inst_raw=None, level=0, is_list=False, no_option=False
    ):
        """
        Recursive helper method for instruction logging.

        Parameters
        ----------
        inst : dict
            The normalized/processed instructions.
        has_inst_raw : bool
            Flag indicating if raw instructions has been passed to _log_instructions().
        inst_raw : dict, optional
            The raw instructions, by default None.
        level : int, optional
            Level used for log indentation where one level corresponds to two spaces, by default 0.
        is_list : bool, optional
            Flag indicating if the current item is part of a list, by default False.
        no_option : bool
            Flag indicating if an item should be treated as a Connect agent option or as a generic data structure, by default False.
        """
        istr = " " * level * 2
        self._cdb.print_log("")
        if is_list:
            iterable = enumerate(inst)
            format_key = lambda idx: f"{istr}({idx+1})"
            get_raw_value = lambda idx: inst_raw[idx] if inst_raw else None
        else:
            iterable = inst.items()
            format_key = lambda k: f"{istr}{k}: "
            get_raw_value = lambda k: (
                inst_raw.get(k, "") if isinstance(inst_raw, dict) else inst_raw
            )
        for k, v in iterable:
            s_option = "" if no_option else format_key(k)
            self._cdb.print_log(f"{s_option:<{self._col_widths[0]}}", end="")
            v_raw = get_raw_value(k)
            if isinstance(v, dict) and len(v) > 0:
                if not isinstance(v_raw, dict) and has_inst_raw:
                    self._cdb.print_log(f">{v_raw}<", end="")
                if k in self._no_option_list:
                    self._log_instructions_r(
                        v, has_inst_raw, v_raw, level + 1, no_option=True
                    )
                else:
                    self._log_instructions_r(v, has_inst_raw, v_raw, level + 1)
            elif isinstance(v, list) and len(v) > 0:
                self._log_instructions_r(
                    v, has_inst_raw, v_raw, level + 1, is_list=True
                )
            else:
                if no_option:
                    s_input = f">{k}<: >{v_raw}<" if inst_raw else ""
                    s_processed = f">{k}<: >{v}<"
                else:
                    s_input = f">{v_raw}<" if isinstance(inst_raw, (dict, list)) else ""
                    s_processed = f">{v}<"
                if has_inst_raw:
                    self._cdb.print_log(
                        f"{s_input:<{self._col_widths[1]}}{s_processed}"
                    )
                else:
                    self._cdb.print_log(f"{s_processed}")

    def _log_instructions(self, inst, inst_raw=None, description=None):
        """
        Logs raw and processed instructions in a table format. If inst_raw is
        None, only the instructions given in inst are printed to the log.

        Parameters
        ----------
        inst : dict
            The normalized/processed instructions.
        inst_raw : dict, optional
            The raw instructions, by default None.
        description : str, optional
            A describtion to be printed to the table header or the Connect agent class if omitted, by default None.
        """

        if description is None:
            description = f"{type(self).__name__}:"

        header = f"{'Option':<{self._col_widths[0]}}"
        ruler = (
            "-" * sum(self._col_widths[:2])
            if inst_raw is None
            else "-" * sum(self._col_widths)
        )
        if inst_raw is not None:
            header += f"{'Input':<{self._col_widths[1]}}"
        header += "Processed Input"
        self._cdb.print_log("")
        self._cdb.print_log(ruler)
        self._cdb.print_log(f"{description}")
        self._cdb.print_log(header)
        self._cdb.print_log(ruler, end="")

        if isinstance(inst, dict):
            self._log_instructions_r(inst, inst_raw is not None, inst_raw)
        else:
            self._cdb.print_log(
                f"Warning: Can not log instructions because type was not 'dict' but {type(inst).__name__}."
            )

        self._cdb.print_log(ruler + "\n")

    def _connect_error(self, msg):
        """
        Raises a GamsConnectException.

        Parameters
        ----------
        msg : str
            Message for the exception.

        Raises
        ----------
        GamsConnectException
            Always.
        """
        raise GamsConnectException(msg, traceback=self._trace > 0)

    def _describe_container(self, m, msg):
        """
        Logs the status of a gams.transfer.Container

        Parameters
        ----------
        m : gams.transfer.Container
            The Container to be used.
        msg : str
            A custom message to be printed to the log.
        """
        try:
            with pd.option_context("display.max_columns", None):
                self._cdb.print_log(f"{msg}\n")
                if len(m.listSets()):
                    self._cdb.print_log(f"Sets:\n{      m.describeSets()      }\n")
                if len(m.listAliases()):
                    self._cdb.print_log(f"Aliases:\n{   m.describeAliases()   }\n")
                if len(m.listParameters()):
                    self._cdb.print_log(f"Parameters:\n{m.describeParameters()}\n")
                if len(m.listEquations()):
                    self._cdb.print_log(f"Equations:\n{ m.describeEquations() }\n")
                if len(m.listVariables()):
                    self._cdb.print_log(f"Variables:\n{ m.describeVariables() }\n")
        except Exception as e:
            self._cdb.print_log(
                f"Exception in ConnectDatabase._describe_container turned into warning: {e}\n"
            )

    def _pandas_version_before(self, pandas_version, version_string):
        """
        Checks if the installed pandas version is before the given version string x.y.

        Parameters
        ----------
        pandas_version : str
            Installed pandas version.
        version_string : str
            Pandas version to check agains in the format x.y.

        Returns
        ----------
        bool
            True if pandas version is before version string and otherwise False.
        """
        pd_ver = list(map(int, pandas_version.split(".")))
        ver = list(map(int, version_string.split(".")))
        if pd_ver[0] < ver[0] or (pd_ver[0] == ver[0] and pd_ver[1] < ver[1]):
            return True
        return False

    def _transform_sym_none_to_empty(self, sym):
        """
        Sets the records of a symbol to an empty DataFrame
        with appropriate column names if the given records are None.

        Parameters
        ----------
        sym : gams.transfer.Alias, gams.transfer.Equation, gams.transfer.Parameter, gams.transfer.Set, gams.transfer.Variable
            Symbol to be checked for None records.
        """
        if sym.records is None:
            sym.setRecords(self._sym_records_no_none(sym, False))

    def _sym_records_no_none(self, sym, set_dtypes=True):
        """
        Returns the records of a symbol or an empty DataFrame
        with appropriate column names for None records.

        Parameters
        ----------
        sym : gams.transfer.Alias, gams.transfer.Equation, gams.transfer.Parameter, gams.transfer.Set, gams.transfer.Variable
            Symbol to be checked for None records.
        set_dtypes : bool, optional
            Sets gams.transfer-like column types if True, by default True.

        Returns
        ----------
        pandas.DataFrame
            The DataFrame of the symbol if records are not None, otherwise an empty DataFrame.
        """
        if sym.records is None:
            attributes = sym._attributes
            cols = generate_unique_labels(sym.domain_names) + attributes
            df = pd.DataFrame(columns=cols)
            if set_dtypes:  # set column dtypes as gams.transfer would do
                for col in cols[: sym.dimension]:
                    df[col] = df[col].astype("category")
                if isinstance(sym, (gt.Parameter, gt.Variable, gt.Equation)):
                    for col in attributes:
                        df[col] = df[col].astype(float)
                elif isinstance(
                    sym, gt.UniverseAlias
                ):  # nothing to do for UniverseAlias
                    pass
                else:  # sets, alias
                    df[attributes[0]] = df[attributes[0]].astype(object)
        else:
            df = sym.records
        return df

    def _replace_no_warn(self, df, vs, mask=None):
        """
        Helper method for _apply_value_substitutions(). Substitutes values in the last column of df
        as provided in vs and returns the modified DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to be used for replacing values in its last column.
        vs : dict
            Dictionary containing the keys that will be replaced by their values.
        mask : numpy.ndarray, optional
            A numpy mask that can be used to exclude certain value positions from the substitution, by default None.

        Returns
        ----------
        pandas.DataFrame
            The DataFrame with the replaced values.
        """
        if vs and len(vs) > 0:
            if df[df.columns[-1]].dtype != object and any(
                isinstance(v, str) for v in vs.values()
            ):
                for k, v in vs.items():
                    if isinstance(v, str) and k in df[df.columns[-1]].values:
                        df[df.columns[-1]] = df[df.columns[-1]].astype(object)
                        break
            if mask is None:
                # pandas-version-check
                if self._pandas_version_before(pd.__version__, "2.2"):  # pandas < 2.2.0
                    df.iloc[:, -1] = df.iloc[:, -1].replace(vs)
                else:  # pandas >= 2.2.0
                    with pd.option_context("future.no_silent_downcasting", True):
                        df.iloc[:, -1] = df.iloc[:, -1].replace(vs).infer_objects()
            else:
                # pandas-version-check
                if self._pandas_version_before(pd.__version__, "2.2"):  # pandas < 2.2.0
                    df.iloc[~mask, -1] = df.iloc[~mask, -1].replace(vs)
                else:  # pandas >= 2.2.0
                    with pd.option_context("future.no_silent_downcasting", True):
                        df.iloc[~mask, -1] = (
                            df.iloc[~mask, -1].replace(vs).infer_objects()
                        )
        return df

    def _apply_value_substitutions(
        self,
        df,
        value_subs,
        sym_type,
        sv_eps=gt.SpecialValues.EPS,
        sv_na=gt.SpecialValues.NA,
        sv_undef=gt.SpecialValues.UNDEF,
        sv_posinf=gt.SpecialValues.POSINF,
        sv_neginf=gt.SpecialValues.NEGINF,
    ):
        """
        Substitutes values in the last column of df as provided in value_subs and returns the modified DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame on which the value substitutions is applied assuming that the last column contains the values.
        value_subs : dict
            Dictionary containing keys to be substituted by values. For GAMS special values, "EPS', "NA", "UNDEF", "INF", and "-INF"
            should be used as keys in the dictionary.
        sym_type : str
            Symbol type. Can be either "par" or "set".
        sv_eps : str, int, float, optional
            Default value used for replacing EPS values (gams.transfer.SpecialValues.EPS) in case "EPS" is not contained in value_subs, by default gams.transfer.SpecialValues.EPS.
        sv_na : str, int, float, optional
            Default value used for replacing NA values (gams.transfer.SpecialValues.NA) in case "NA" is not contained in value_subs, by default gams.transfer.SpecialValues.NA.
        sv_undef : str, int, float, optional
            Default value used for replacing UNDEF values (gams.transfer.SpecialValues.UNDEF) in case "UNDEF" is not contained in value_subs, by default gams.transfer.SpecialValues.UNDEF.
        sv_posinf : str, int, float, optional
            Default value used for replacing INF values (gams.transfer.SpecialValues.POSINF) in case "INF" is not contained in value_subs, by default gams.transfer.SpecialValues.POSINF.
        sv_neginf : str, int, float, optional
            Default value used for replacing -INF values (gams.transfer.SpecialValues.NEGINF) in case "-INF" is not contained in value_subs, by default gams.transfer.SpecialValues.NEGINF.

        Returns
        -------
        pandas.DataFrame
            The modified DataFrame with applied substitutions for the last column. Depending on the used substitutions, the dtype of
            that column might be changed to object.
        """

        vs = value_subs.copy() if value_subs is not None else {}
        if vs:  # convert int/complex to float
            vs = {
                k: float(v) if isinstance(v, (int, complex)) else v
                for k, v in value_subs.items()
            }
        if sym_type == "par":

            def replace_sv(df, eps_val, na_val, undef_val, posinf_val, neginf_val):
                arr = df.iloc[:, -1].values

                # create special values masks
                eps_mask = gt.SpecialValues.isEps(arr)
                has_eps = eps_mask.any()

                na_mask = gt.SpecialValues.isNA(arr)
                has_na = na_mask.any()

                undef_mask = gt.SpecialValues.isUndef(arr)
                has_undef = undef_mask.any()

                posinf_mask = gt.SpecialValues.isPosInf(arr)
                has_posinf = posinf_mask.any()

                neginf_mask = gt.SpecialValues.isNegInf(arr)
                has_neginf = neginf_mask.any()

                # replace special values
                if has_eps or has_na or has_undef or has_posinf or has_neginf:
                    if (
                        has_eps
                        and isinstance(eps_val, str)
                        or has_na
                        and isinstance(na_val, str)
                        or has_undef
                        and isinstance(undef_val, str)
                        or has_posinf
                        and isinstance(posinf_val, str)
                        or has_neginf
                        and isinstance(neginf_val, str)
                    ):
                        arr = arr.astype(object)
                    mask = eps_mask | na_mask | undef_mask | posinf_mask | neginf_mask
                    if has_eps:
                        arr[eps_mask] = eps_val
                    if has_na:
                        arr[na_mask] = na_val
                    if has_undef:
                        arr[undef_mask] = undef_val
                    if has_posinf:
                        arr[posinf_mask] = posinf_val
                    if has_neginf:
                        arr[neginf_mask] = neginf_val
                    df[df.columns[-1]] = arr
                    return df, mask
                return df, None

            # determine special values substitutions
            gt_eps_in_vs = any(
                not isinstance(k, str) and gt.SpecialValues.isEps(k) for k in vs.keys()
            )
            if "EPS" in vs.keys():
                if gt_eps_in_vs:
                    self._cdb.print_log(
                        f'Warning: "EPS" ({vs["EPS"]}) overwrites -0.0 ({vs[gt.SpecialValues.EPS]}) in valueSubstitutions.'
                    )
                    del vs[gt.SpecialValues.EPS]
                eps_val = vs["EPS"]
                del vs["EPS"]
            elif gt_eps_in_vs:
                eps_val = vs[gt.SpecialValues.EPS]
                del vs[gt.SpecialValues.EPS]
            else:
                eps_val = sv_eps

            if "NA" in vs.keys():
                na_val = vs["NA"]
                del vs["NA"]
            else:
                na_val = sv_na

            if "UNDEF" in vs.keys():
                undef_val = vs["UNDEF"]
                del vs["UNDEF"]
            else:
                undef_val = sv_undef

            if "INF" in vs.keys():
                if gt.SpecialValues.POSINF in vs:
                    self._cdb.print_log(
                        f'Warning: "INF" ({vs["INF"]}) overwrites .inf ({vs[float("inf")]}) in valueSubstitutions.'
                    )
                    del vs[gt.SpecialValues.POSINF]
                posinf_val = vs["INF"]
                del vs["INF"]
            elif gt.SpecialValues.POSINF in vs:
                posinf_val = vs[gt.SpecialValues.POSINF]
                del vs[gt.SpecialValues.POSINF]
            else:
                posinf_val = sv_posinf

            if "-INF" in vs.keys():
                if gt.SpecialValues.NEGINF in vs:
                    self._cdb.print_log(
                        f'Warning: "-INF" ({vs["-INF"]}) overwrites -.inf ({vs[float("-inf")]}) in valueSubstitutions.'
                    )
                    del vs[gt.SpecialValues.NEGINF]
                neginf_val = vs["-INF"]
                del vs["-INF"]
            elif gt.SpecialValues.NEGINF in vs:
                neginf_val = vs[gt.SpecialValues.NEGINF]
                del vs[gt.SpecialValues.NEGINF]
            else:
                neginf_val = sv_neginf

            # - pandas does not distingish between gt.SpecialValues.NA and gt.SpecialValues.UNDEF and
            #   we have to replace NA manually first.
            # - pandas replace() does not distinguish between +0.0 and -0.0 (gt.SpecialValues.EPS) and we
            #   have to replace EPS manually first.
            # - all other special values (UNDEF, INF, -INF) are replaced manually as well for consistency and
            #   performance reasons
            df, mask = replace_sv(
                df, eps_val, na_val, undef_val, posinf_val, neginf_val
            )
            df = self._replace_no_warn(df, vs, mask)
        else:  # set
            df = self._replace_no_warn(df, vs)

        return df

    def _check_symbol_exists(self, sym_names):
        """
        Raises a GamsConnectException if a single symbol or at least one symbol
        of a given list of symbols does exist in the Connect Database.

        Parameters
        ----------
        sym_names : str, list[str]
            A list of symbol names or a single symbol name to be checked.

        Raises
        ----------
        GamsConnectException
            If at least one symbol already exists.
        """
        sym_list = sym_names if isinstance(sym_names, list) else [sym_names]
        existing_symbols = [s for s in sym_list if s in self._cdb.container]
        if len(existing_symbols) == 1:
            self._connect_error(
                f"A symbol with name >{existing_symbols[0]}< already exists in the Connect Database."
            )
        elif len(existing_symbols) > 1:
            self._connect_error(
                f"Symbols >{existing_symbols}< already exist in the Connect Database."
            )

    def _update_sym_inst(self, sym_inst, root_inst):
        """
        Updates None values in the symbols scope instructions with the corresponding values
        from the root scope for all keys that exist in both instruction dictionaries.
        This method is not recursive and considers only the first level of the provided
        dictionaries. sym_inst is updated inplace and also returned.

        Parameters
        ----------
        sym_inst : dict
            Symbols instructions to be updated.
        root_inst : dict
            Root instructions to be used for updating sym_inst

        Returns
        ----------
        dict
            The updated sym_inst dictionary
        """
        keys = [
            k for k in sym_inst.keys() if k in root_inst
        ]  # all keys that exist in both dictionaries
        for k in keys:
            if sym_inst[k] is None:
                sym_inst[k] = root_inst[k]
        return sym_inst

    def _dict_get(self, d, key, default):
        """
        Like dict.get() but handles keys with None value as if they were missing.

        Parameters
        ----------
        d : dict
            Dictionary to be used.
        key : str
            The key to be found in d.
        default : int, str, float
            Default value to be returned in case d.get(key) is None.

        Returns
        ----------
        int, str, float
            d[key] if key is in d and the value is not None, default otherwise.
        """
        return default if d.get(key) is None else d[key]

    def open(self):
        """
        Called by the ConnectDatabase before execute().
        """

    @abstractmethod
    def execute(self):
        """
        Called by the ConnectDatabase after open() and before close(). This abstract method needs to be implemented by a subclass.
        """

    def close(self):
        """
        Called by the ConnectDatabase after execute().
        """
