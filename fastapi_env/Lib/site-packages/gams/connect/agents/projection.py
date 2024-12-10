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

import copy
import re
from gams.connect.agents.connectagent import ConnectAgent
import gams.transfer as gt
import pandas as pd


class Projection(ConnectAgent):

    def __init__(self, cdb, inst):
        super().__init__(cdb, inst)
        inst_raw = inst
        inst = self._normalize_instructions(inst)
        self._parse_options(inst)
        if self._trace > 0:
            self._log_instructions(inst, inst_raw)
        if self._trace > 3:
            pd.set_option("display.max_rows", None, "display.max_columns", None)

    def _parse_options(self, inst):
        self._aggregation_method = inst["aggregationMethod"]
        self._as_set = inst["asSet"]
        self._name = inst["name"]
        self._new_name = inst["newName"]
        self._text = inst["text"]
        self._trace = inst["trace"]

    def _generate_text(self, df, ssym, sdom, suffix_list, suffix_to_index):
        """Generates set element text."""

        if (
            (isinstance(ssym, gt.Set) and not self._text in [None, ""])
            or (
                isinstance(ssym, (gt.Variable, gt.Equation))
                and suffix_list
                and not suffix_to_index
                and not self._text in [None, ""]
            )
            or (isinstance(ssym, gt.Parameter) and not self._text in [None, ""])
        ):
            df.columns = [*df.columns[:-1], "element_text"]
            df["element_text"] = df["element_text"].astype(str)
            sdom.append("element_text")
            execcmd = 'df["element_text"] = ("' + self._text + '")'
            for i, r in enumerate(sdom):
                execcmd = execcmd.replace(
                    "{" + r + "}",
                    '" + df[df.columns[' + str(i) + ']].astype(str) + "',
                )
            exec(execcmd)
            if self._trace > 2:
                self._cdb.print_log(f"DataFrame after text adjustment:\n{df}")

        return df

    def _combine_scalars(self):
        """Aggregates a list of scalars of the same type into a 1-dimensional symbol (of the same type) that holds the symbol names as labels."""

        symrecords_list = []
        sym_types = []
        for sym_name in self._name:
            if sym_name not in self._cdb.container:
                self._connect_error(
                    f"Symbol '{sym_name}' not found in Connect database."
                )
            sym = self._cdb.container[sym_name]
            if sym.dimension != 0:
                self._connect_error(
                    f"Symbol '{sym_name}' needs to be a scalar when specified in <name> using a list."
                )
            sym_types.append(type(sym))
            df = self._sym_records_no_none(sym).copy(deep=True)
            symrecords_list.append(df)
        if not all(t == sym_types[0] for t in sym_types):
            self._connect_error(
                "All symbols need to be of the same type when specified in <name> using a list."
            )

        df = pd.concat(symrecords_list, ignore_index=True)
        df.insert(0, "uni_0", self._name)
        sym0 = self._cdb.container[self._name[0]]

        if isinstance(sym0, gt.Parameter):
            gt.Parameter(
                self._cdb.container,
                self._new_name,
                ["*"],
                records=df,
            )
        elif isinstance(sym0, gt.Equation):
            gt.Equation(
                self._cdb.container,
                self._new_name,
                sym0.type,
                ["*"],
                records=df,
            )
        elif isinstance(sym0, gt.Variable):
            gt.Variable(
                self._cdb.container,
                self._new_name,
                sym0.type,
                ["*"],
                records=df,
            )

    def _split_index(self, match, symname, allow_duplicates=False):
        """Splits provided index space into a list of indices. Return an empty list if no index space is provided."""

        if match.group("index") is not None:
            index = [d.strip() for d in match.group("index").split(",")]
            if allow_duplicates:
                return index

            for i in index:
                if index.count(i) > 1:
                    self._connect_error(
                        f"Multiple use of index >{i}< in index list of symbol >{symname}<."
                    )
            return index
        else:
            return []

    def _process_symbol_name(self):
        """Processes strings provided by the name/newName option. Splits name/newName into the symbol name, suffix and index list."""

        regex = r"(?P<name>[a-zA-Z0-9_]+)(\.?(?P<suffix>([a-zA-Z]*)|(\[[a-zA-Z,\s]*\])))?(\((?P<index>[a-zA-Z0-9_,\s]*)\))?"
        ms = re.fullmatch(regex, self._name)
        if not ms:
            self._connect_error(f"Invalid <name>: >{self._name}<.")
        mt = re.fullmatch(regex, self._new_name)
        if not mt:
            self._connect_error(f"Invalid <newName>: >{self._new_name}<.")

        # NAME
        ssym_name = ms.group("name")
        if ssym_name not in self._cdb.container:
            self._connect_error(f"Symbol '{ssym_name}' not found in Connect database.")
        ssym = self._cdb.container[ssym_name]
        tsym_name = mt.group("name")

        # INDEX
        # Source symbol
        sindex_list = self._split_index(ms, ssym_name)

        # Target symbol
        tindex_list = self._split_index(mt, tsym_name, allow_duplicates=True)

        if len(sindex_list) != ssym.dimension:
            self._connect_error(
                f"Number of provided indices for symbol >{ssym_name}< <> dimension of the symbol ({len(sindex_list)}<>{ssym.dimension})."
            )
        if set(tindex_list) - set(sindex_list):
            self._connect_error(
                f"Unknown index >{(set(tindex_list) - set(sindex_list))}< in <newName>: >{self._new_name}<."
            )
        index_map = [sindex_list.index(d) for d in tindex_list]
        tsym_domain = [ssym.domain[d] for d in index_map]

        # SUFFIX
        suffix_dict = {
            "l": "level",
            "m": "marginal",
            "lo": "lower",
            "up": "upper",
            "scale": "scale",
            "all": "all",
        }
        attribute_list = [a for a in suffix_dict.values() if a != "all"]

        if mt.group("suffix"):
            self._connect_error(f"No suffix allowed on <newName>: >{self._new_name}<.")
        suffix = ms.group("suffix")
        if suffix == "":
            suffix_list = []

        suffix_to_index = False
        if suffix:
            if not isinstance(ssym, (gt.Variable, gt.Equation)):
                self._connect_error(
                    f"Suffix given but symbol >{ssym_name}< is not a variable or an equation."
                )

            if re.search(r"[\[\]]", suffix):
                suffix_to_index = True
                tsym_domain.append("attribute")
                suffix = re.sub(r"[\[\]]", "", suffix)
                if suffix == "":
                    self._connect_error("Suffix list is empty.")
                else:
                    suffix_list = list(
                        dict.fromkeys(s.strip() for s in suffix.split(","))
                    )
            else:
                suffix_list = [suffix]

            for s in suffix_list:
                if s not in suffix_dict.keys():
                    self._connect_error(
                        f"Unknown suffix >{s}< (use {', '.join([s for s in suffix_dict.keys()])})."
                    )
            # resolve v.all and v.[all]
            if "all" in suffix_list:
                suffix_list = attribute_list
                if not suffix_to_index:  # might have been added before already
                    suffix_to_index = True
                    tsym_domain.append("attribute")
            else:
                suffix_list = list(map(suffix_dict.get, suffix_list))

        if self._trace > 1:
            self._cdb.print_log(
                "Processed <name>:"
                f"\n  name: >{ssym_name}<"
                f"\n  index: >{sindex_list}<"
                f"\n  suffix: >{suffix_list}<"
                f"\n  suffix to index: >{suffix_to_index}<"
                "\n"
            )
            self._cdb.print_log(
                "Processed <newName>:"
                f"\n  name: >{tsym_name}<"
                f"\n  index: >{tindex_list}<"
                "\n"
            )

        self._check_symbol_exists(tsym_name)

        return (
            ssym,
            ssym_name,
            sindex_list,
            suffix_list,
            suffix_to_index,
            tsym_name,
            tindex_list,
            index_map,
            tsym_domain,
        )

    def _create_target_symbol(
        self, ssym, ssym_name, tsym_name, tsym_domain, suffix_list
    ):
        """Create target symbol in Connect container."""

        if self._as_set or isinstance(ssym, gt.Set):
            tsym = gt.Set(self._cdb.container, tsym_name, tsym_domain)
        elif suffix_list or isinstance(ssym, gt.Parameter):
            tsym = gt.Parameter(self._cdb.container, tsym_name, tsym_domain)
        elif isinstance(ssym, gt.Equation):
            tsym = gt.Equation(self._cdb.container, tsym_name, ssym.type, tsym_domain)
        elif isinstance(ssym, gt.Variable):
            tsym = gt.Variable(self._cdb.container, tsym_name, ssym.type, tsym_domain)
        else:
            self._connect_error(
                f"Projection can't handle symbol type >{type(ssym)}< of symbol >{ssym_name}<."
            )
        if self._trace > 1:
            self._cdb.print_log(
                f"Created >{tsym_name}< as {len(tsym_domain)}-dim {type(tsym)}.\n"
            )

        return tsym

    def _apply_aggregation_method(self, df, ssym_name, index_map):
        """Applies selected aggregation method."""

        if len(index_map) > 0:
            df = df.groupby(
                [self._cdb.container[ssym_name].domain_labels[d] for d in index_map]
            )
        if not hasattr(df, self._aggregation_method):
            self._connect_error(
                f"Invalid aggregationMethod >{self._aggregation_method}<."
            )
        func = getattr(df, self._aggregation_method)
        if not callable(func):
            self._connect_error(
                f"Invalid aggregationMethod >{self._aggregation_method}<. Not callable."
            )
        df = func()
        if self._trace > 2:
            self._cdb.print_log(f"DataFrame after aggregation:\n{df}")
        return df

    def _drop_text(self, df, ssym, suffix_list, suffix_to_index):
        """Drops set element text."""

        if isinstance(ssym, gt.Set) and self._text == "":
            df.drop(columns=df.columns[-1], inplace=True)
        elif isinstance(ssym, (gt.Variable, gt.Equation)) and suffix_to_index:
            df.drop(columns=df.columns[-1], inplace=True)
        elif (
            isinstance(ssym, (gt.Variable, gt.Equation))
            and suffix_list
            and self._text in [None, ""]
        ):
            df.drop(columns=df.columns[-1], inplace=True)
        elif isinstance(ssym, (gt.Variable, gt.Equation)) and not suffix_list:
            df.drop(
                columns=["level", "marginal", "lower", "upper", "scale"],
                inplace=True,
            )
        elif isinstance(ssym, gt.Parameter) and self._text in [None, ""]:
            df.drop(columns=df.columns[-1], inplace=True)

        return df

    def _apply_categories(self, ssym, tsym, suffix_to_index, suffix_list, index_map):
        """Applies categories from the source symbol to the domains of the target symbol."""

        if tsym.dimension > 0:
            for i in range(tsym.dimension):
                if suffix_to_index and i == tsym.dimension - 1:
                    cats = suffix_list
                else:
                    cats = ssym.records[
                        ssym.records.columns[index_map[i]]
                    ].cat.categories

                tsym.records.isetitem(
                    i,
                    tsym.records.iloc[:, i].astype(
                        pd.CategoricalDtype(
                            categories=cats,
                            ordered=True,
                        )
                    ),
                )

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")

        # list of scalars into a 1-dim parameter/var/equ
        if isinstance(self._name, list):
            self._combine_scalars()

            if self._trace > 2:
                self._cdb.print_log(
                    f"Connect Container symbol={self._new_name}:\n {self._cdb.container[self._new_name].records}\n"
                )

            return

        (
            ssym,
            ssym_name,
            sindex_list,
            suffix_list,
            suffix_to_index,
            tsym_name,
            tindex_list,
            index_map,
            tsym_domain,
        ) = self._process_symbol_name()

        # Get unique index, map lists
        tindex_list_unq = list(dict.fromkeys(tindex_list))  # (i,j,i) -> (i,j)
        index_map_unq = list(dict.fromkeys(index_map))  # (0,1,0) -> (0,1)

        if tindex_list_unq != tindex_list:  # duplicate index (e.g. newName: p(i,j,i))
            if self._trace > 1:
                self._cdb.print_log(
                    f"Duplicate indices found. Processing symbol without duplicate indices: {tsym_name}({','.join(tindex_list)}) -> {tsym_name}({','.join(tindex_list_unq)}).\n"
                )

        tsym = self._create_target_symbol(
            ssym, ssym_name, tsym_name, tsym_domain, suffix_list
        )

        assert len(index_map) == tsym.dimension or (
            len(index_map) + 1 == tsym.dimension and suffix_to_index
        ), "Number of domains for <newName> <> dimension of <newName>"
        assert len(tsym_domain) == tsym.dimension or (
            len(tsym_domain) + 1 == tsym.dimension and suffix_to_index
        ), "Number of domains for <newName> <> dimension of <newName>"
        assert (
            not suffix_list or isinstance(tsym, gt.Parameter) or self._as_set
        ), "Type of <newName> needs to be parameter or asSet needs to be True"
        assert (
            suffix_list
            or suffix_to_index
            or self._as_set
            or isinstance(ssym, type(tsym))
        ), "No suffix, asSet: False but type of <name> <> type of <newName>"

        df = copy.deepcopy(self._cdb.container[ssym_name].records)
        # For symbols with None records or empty dataframe, an empty df is assigned then returned
        if df is None or df.empty:
            self._transform_sym_none_to_empty(tsym)
            return

        if suffix_list:
            suffixes_to_drop = set(
                ["level", "marginal", "lower", "upper", "scale"]
            ) - set(suffix_list)
            df.drop(columns=list(suffixes_to_drop), inplace=True)
            if self._trace > 2:
                self._cdb.print_log(f"DataFrame after dropping suffixes:\n{df}")

        if isinstance(tsym, gt.Set):
            df = self._generate_text(
                df, ssym, sindex_list, suffix_list, suffix_to_index
            )

        if self._aggregation_method is None:  # no aggregation
            permutation = index_map_unq != list(range(len(index_map_unq))) or len(
                sindex_list
            ) > len(tindex_list_unq)
            if permutation:
                if self._trace > 1:
                    self._cdb.print_log("Permutation only.")
                attributes = df.columns.tolist()[ssym.dimension :]
                cols_permuted = [
                    df.columns.tolist()[i] for i in index_map_unq
                ] + attributes
                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame before permutation:\n{df}")
                if self._trace > 1:
                    self._cdb.print_log(f"Column permutation:\n{cols_permuted}")
                df = df.reindex(columns=cols_permuted)
                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame after permutation:\n{df}")

            if suffix_to_index:
                # stack suffix index
                if ssym.dimension == 0:
                    # source and target symbols have 0 dimensions (scalar)
                    df = df.stack().droplevel(0)
                    df = list(dict(df).items())
                else:
                    if len(index_map_unq) > 0:
                        new_index = [
                            df.columns.tolist()[i] for i in range(len(index_map_unq))
                        ]
                        df.set_index(new_index, inplace=True)
                        df = df.stack().reset_index()
                    else:
                        df = df.stack().droplevel(0)
                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame after stacking suffix index:\n{df}")

        else:
            # TODO: Raise error if sets, variable or equations (without suffix) are not used with first/last aggregation
            drop_cols = self._cdb.container[ssym_name].domain_labels[: ssym.dimension]
            df[drop_cols] = df[drop_cols].astype(str)

            if (
                tsym.dimension == 0 or (tsym.dimension == 1 and suffix_to_index)
            ) and self._aggregation_method in [
                "first",
                "last",
            ]:
                # target symbol has 0 dimensions (scalar) and aggregation first/last -> fast aggregation

                df.drop(columns=drop_cols, inplace=True)
                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame after dropping columns:\n{df}")
                if self._aggregation_method == "first":
                    df = df.iloc[0]
                else:
                    df = df.iloc[-1]
                if isinstance(tsym, (gt.Variable, gt.Equation)):
                    df = dict(df)
                elif suffix_to_index:
                    df = list(dict(df).items())
                if self._trace > 2:
                    self._cdb.print_log(
                        f"DataFrame after first/last aggregation:\n{df}"
                    )
            else:
                if ssym.dimension != 0:
                    multi_index = pd.MultiIndex.from_frame(
                        df[self._cdb.container[ssym_name].domain_labels]
                    )
                    df.set_index(multi_index, inplace=True)
                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame after .set_index():\n{df}")

                df.drop(columns=drop_cols, inplace=True)
                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame after dropping columns:\n{df}")

                df = self._apply_aggregation_method(df, ssym_name, index_map_unq)

                if isinstance(df, pd.DataFrame):
                    if suffix_to_index:
                        df = df.stack()
                        if self._trace > 2:
                            self._cdb.print_log(
                                f"DataFrame after stacking suffix index:\n{df}"
                            )

                    df = df.reset_index(drop=False)
                    if self._trace > 2:
                        self._cdb.print_log(f"DataFrame after .reset_index():\n{df}")

        if isinstance(df, pd.DataFrame) and isinstance(tsym, gt.Set):
            df = self._drop_text(df, ssym, suffix_list, suffix_to_index)

        if self._trace > 2:
            self._cdb.print_log(f"DataFrame before .setRecords():\n{df}")

        if tindex_list_unq != tindex_list:  # duplicate index (e.g. newName: p(i,j,i))
            if self._trace > 1:
                self._cdb.print_log(
                    f"Restoring duplicate indices: {tsym_name}({','.join(tindex_list_unq)}) -> {tsym_name}({','.join(tindex_list)}).\n"
                )
            new_index = [tindex_list_unq.index(i) for i in tindex_list]
            new_index = [df.columns.tolist()[x] for x in new_index]
            new_cols = new_index + df.columns.tolist()[len(tindex_list_unq) :]
            df = df[new_cols]
        tsym.setRecords(df)

        self._apply_categories(ssym, tsym, suffix_to_index, suffix_list, index_map)

        if self._trace > 2:
            self._cdb.print_log(
                f"Connect Container symbol={tsym_name}:\n {tsym.records}\n"
            )
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
