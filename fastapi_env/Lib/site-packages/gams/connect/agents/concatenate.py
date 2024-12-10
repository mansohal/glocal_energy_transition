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

import re
import warnings
import gams.transfer as gt
import pandas as pd
from gams.connect.agents.connectagent import ConnectAgent
import numpy as np


class Concatenate(ConnectAgent):
    def __init__(self, cdb, inst):
        super().__init__(cdb, inst)
        self.__gt2pytypemap__ = {gt.Set: "set", gt.Parameter: "parameter"}
        inst_raw = inst
        inst = self._normalize_instructions(inst)
        self._parse_options(inst)
        if self._trace > 0:
            self._log_instructions(inst, inst_raw)
        if self._trace > 3:
            pd.set_option("display.max_rows", None, "display.max_columns", None)

    def _parse_options(self, inst):
        # root options
        self._output_dimensions = inst["outputDimensions"]
        self._dimension_map = self._dict_get(inst, "dimensionMap", {})
        self._universal_dimension = inst["universalDimension"]
        self._emptyuel = inst["emptyUel"]
        self._output_name = {
            "set": inst["setName"],
            "parameter": inst["parameterName"],
        }
        self._symbols_dimension = inst["symbolsDimension"]
        self._skip = inst["skip"]
        self._trace = inst["trace"]
        self._dim_start = int(self._symbols_dimension)

        # symbol options
        self._symbols = inst["symbols"]
        self._write_all = self._symbols == "all"

    def _create_symbols_list(self) -> None:
        """Creates the symbols list"""

        if self._write_all:
            self._symbols = []
            for name, sym in self._cdb.container.data.items():
                if isinstance(sym, (gt.Set, gt.Parameter)):
                    self._symbols.append({"name": name})

        remove_symbols = []  # remove symbols with no data
        for i, sym_opt in enumerate(self._symbols):
            regex = r"(?P<name>[a-zA-Z0-9_]+)?(\((?P<domains>[a-zA-Z0-9_,\s]*)\))?"
            ms = re.fullmatch(regex, sym_opt["name"])
            if ms is None:
                self._connect_error(f"Invalid symbol name {sym_opt['name']}.")
            sym_opt["sname"] = ms.group("name")

            if sym_opt["sname"] not in self._cdb.container:
                self._connect_error(
                    f"Symbol '{sym_opt['sname']}' not found in Connect database."
                )

            sym = self._cdb.container[sym_opt["sname"]]

            if not isinstance(sym, (gt.Set, gt.Parameter)):
                self._connect_error(
                    f"Symbol type >{type(sym)}< of symbol >{sym_opt['sname']}< is not supported. Supported symbol types are sets and parameters. If you would like to concatenate variables or equations, use Connect Agent Projection to turn these into parameters."
                )

            if self._skip == "set" and isinstance(sym, gt.Set):  # skip sets
                remove_symbols.append(i)
                continue
            if self._skip == "par" and isinstance(sym, gt.Parameter):  # skip parameters
                remove_symbols.append(i)
                continue

            if self._trace > 2:
                self._cdb.print_log(
                    f"Connect Container symbol={sym_opt['sname']}:\n {sym.records}\n"
                )

            if ms.group("domains") is not None:
                sym_opt["dim"] = [dom.strip() for dom in ms.group("domains").split(",")]

                if sym.dimension != len(sym_opt["dim"]):
                    self._connect_error(
                        f"Number of specified dimensions of symbol >{sym_opt['name']}< does not correspond to the symbol's number of dimensions in the database ({len(sym_opt['dim'])}<>{sym.dimension})."
                    )

            else:
                sym_opt["dim"] = []
                if (
                    sym.dimension > 0
                ):  # if symbol dim is not specified: use dimension_map to map domains to output dimensions, domains that cannot be mapped will be universal output dimensions
                    sym_opt["dim"] = [
                        self._dimension_map.get(d, d) for d in sym.domain_names
                    ]

        for i in reversed(remove_symbols):
            del self._symbols[i]

    def _create_output_dimensions(self) -> None:
        """Creates output dimensions"""
        # if outputDimensions is all, generate output dimensions from symbol dimensions
        if self._output_dimensions == "all":
            self._output_dimensions = []
            for sym_opt in self._symbols:
                for idx, d in enumerate(sym_opt["dim"]):
                    if d not in self._output_dimensions:
                        self._output_dimensions.append(d)
                    elif self._output_dimensions.count(d) < sym_opt["dim"][
                        : idx + 1
                    ].count(d):
                        self._output_dimensions.append(d)
        else:
            regex = r"([a-zA-Z0-9_]*)"
            invalid_dim = [
                dim for dim in self._output_dimensions if not re.fullmatch(regex, dim)
            ]
            if invalid_dim != []:
                self._connect_error(f"Invalid output dimension(s) >{invalid_dim}<.")

        if "symbols" in self._output_dimensions and self._symbols_dimension:
            self._connect_error("'symbols' is a preserved output dimension.")

    def _make_dimensions_unique(self, dim_list: list) -> list:
        """Makes dimensions unique. Example: ['i', 'j', 'j'] -> ['i', 'j', 'j.1']

        Parameters
        ----------
        dim_list : list
            Dimensions

        Returns
        -------
        list
            Unique dimensions
        """
        cp_dim_list = dim_list.copy()
        counts = {}
        for i, dim in enumerate(cp_dim_list):
            cur_count = counts.get(dim, 0)
            if cur_count > 0:
                cp_dim_list[i] = "%s.%d" % (dim, cur_count)
            counts[dim] = cur_count + 1

        return cp_dim_list

    def _add_universal_dimensions(
        self,
        nb_uni_dim: int,
        unknown_dim: list,
        unique_output_dimensions: list,
    ) -> int:
        """Adds universal dimensions. Also updates the output dimensions with the newly added universal dimensions.

        Parameters
        ----------
        nb_uni_dim : int
            Number of universal dimensions
        unknown_dim : list
            Unknown dimensions
        unique_output_dimensions : list
            Unique output dimensions

        Returns
        -------
        int
            Updated number of universal dimensions
        list
            Updated unique output dimensions
        """
        for i in range(nb_uni_dim, len(unknown_dim)):
            uni_name = f"{self._universal_dimension}_{i}"
            if uni_name in self._output_dimensions:
                self._connect_error(
                    f"Automatically added universal column >{uni_name}< is already specified under option outputDimensions. Please set another base name for universal dimensions via option universalDimension or rename the output dimension."
                )
            self._output_dimensions.append(uni_name)
            unique_output_dimensions.append(uni_name)
            nb_uni_dim += 1

        return nb_uni_dim, unique_output_dimensions

    def _save_categories(
        self,
        unique_output_dimensions: list,
        dataframes: dict,
        output_types: list,
    ) -> dict:
        """Save categories that might be lost after pandas.concat due to pandas bug https://github.com/pandas-dev/pandas/issues/51362

        Parameters
        ----------
        unique_output_dimensions : list
            Unique output dimensions
        dataframes : dict
            Dictionary of dataframes to be concatenated (by output type)
        output_types : list
            Output types

        Returns
        -------
        dict
            Dictionary that maps dimensions of the output symbols to the union of categories from the input symbols (by output type)
        """

        output_dim_cat_map = {}
        for ot in output_types:
            output_dim_cat_map[ot] = {}
            # initialize mapping
            for i in range(len(unique_output_dimensions)):
                output_dim_cat_map[ot][i + self._dim_start] = []
            for df in dataframes[ot]:
                # iterate over all dimensions except symbols (0) and value/text column (-1) and save categories
                for d in list(df.columns[self._dim_start : -1]):
                    idx = (
                        unique_output_dimensions.index(d) + self._dim_start
                    )  # dimension position in the output symbol
                    dim_series = df[d].cat.remove_unused_categories()
                    output_dim_cat_map[ot][idx].extend(
                        dim_series.cat.categories.tolist()
                    )
            # make categories unique
            for k, v in output_dim_cat_map[ot].items():
                output_dim_cat_map[ot][k] = list(dict.fromkeys(v))

        return output_dim_cat_map

    def _concatenate_dataframes(
        self,
        dataframes: dict,
        output_types: list,
        unique_output_dimensions: list,
        gt_na_values: list,
        output_dim_cat_map: dict,
    ) -> dict:
        """Concatenates dataframes of sets and parameters respectively.

        Parameters
        ----------
        dataframes : dict
            Dictionary of dataframes to be concatenated (by output type)
        output_types : list
            Output types
        unique_output_dimensions : list
            Unique output dimensions
        gt_na_values : list
            gt.SpecialValues.NA to be recovered after pd.concat
        output_dim_cat_map: dict
            categories to be recovered after pd.concat

        Returns
        -------
        dict
            Output symbols
        """
        outputs = {}
        symbols = ["symbols"] if self._symbols_dimension else []
        for ot in output_types:
            val_col = "text" if ot == "set" else "value"
            # pandas-version-check
            with warnings.catch_warnings():  # pandas 2.1.0 has a FutureWarning for concatenating empty DataFrames
                warnings.filterwarnings(
                    "ignore",
                    message=".*The behavior of DataFrame concatenation with empty or all-NA entries is deprecated.*",
                    category=FutureWarning,
                )
                outputs[ot] = pd.DataFrame(
                    pd.concat(dataframes[ot]),
                    columns=symbols + unique_output_dimensions + [val_col],
                )

            # recover gt.SpecialValues.NA after pd.concat
            if ot == "parameter" and any(gt_na_values):
                outputs[ot] = outputs[ot].astype(
                    {"value": np.dtype("object")}
                )  # needs to be data type object for mask to work with gt.SpecialValues.NA
                outputs[ot]["value"] = outputs[ot]["value"].mask(
                    gt_na_values,
                    gt.SpecialValues.NA,
                )
                # outputs[ot].loc[gt_na_values, "value"] = gt.SpecialValues.NA # works in general but not with gt.SpecialValues.NA

            # recover categories if necessary
            for i in list(output_dim_cat_map[ot].keys()):
                if not isinstance(outputs[ot].iloc[:, i].dtype, pd.CategoricalDtype):
                    outputs[ot].isetitem(
                        i,
                        outputs[ot]
                        .iloc[:, i]
                        .astype(
                            pd.CategoricalDtype(
                                categories=output_dim_cat_map[ot][i],
                                ordered=True,
                            )
                        ),
                    )

            # add empty uel to categoricals
            df = outputs[ot]
            for c in df[df.columns[self._dim_start : -1]]:
                if isinstance(df[c].dtype, pd.CategoricalDtype):
                    df[c] = df[c].cat.add_categories(self._emptyuel)

            outputs[ot].reset_index(inplace=True, drop=True)
            outputs[ot][outputs[ot].columns[self._dim_start : -1]] = outputs[ot][
                outputs[ot].columns[self._dim_start : -1]
            ].fillna(self._emptyuel)

        return outputs

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")

        self._create_symbols_list()
        if not self._symbols:
            self._cdb.print_log("No data to concatenate.")
            return

        self._create_output_dimensions()
        unique_output_dimensions = self._make_dimensions_unique(self._output_dimensions)

        # create dataframes to concatenate
        output_types = set()
        dataframes = {"set": [], "parameter": []}  # dataframes to concatenate
        nb_uni_dim = (
            0  # required number of universal dimensions in the output dimensions
        )
        gt_na_values = []  # recover gt.SpecialValues.NA after pd.concat
        for sym_opt in self._symbols:
            sym = self._cdb.container[sym_opt["sname"]]
            output_types.add(self.__gt2pytypemap__[type(sym)])

            if sym.dimension > 0:
                # make symbol dimensions unique
                sym_opt["dim"] = self._make_dimensions_unique(sym_opt["dim"])

                # identify unknown dimensions, unknown dimensions will be aggregated into universal output dimensions
                unknown_dim = [
                    i
                    for i, x in enumerate(sym_opt["dim"])
                    if x not in unique_output_dimensions
                ]
                if nb_uni_dim < len(
                    unknown_dim
                ):  # add universal dimensions if required
                    (
                        nb_uni_dim,
                        unique_output_dimensions,
                    ) = self._add_universal_dimensions(
                        nb_uni_dim, unknown_dim, unique_output_dimensions
                    )
                for i, dim_idx in enumerate(
                    unknown_dim
                ):  # overwrite current dimension name with universal dimension name
                    sym_opt["dim"][dim_idx] = f"{self._universal_dimension}_{i}"

                if self._trace > 1:
                    self._cdb.print_log(
                        f"Dimension(s) of symbol={sym_opt['name']}:\n {sym_opt['dim']}\n"
                    )

            sym_records = self._sym_records_no_none(sym).copy(deep=True)
            val_col = "text" if isinstance(sym, gt.Set) else "value"
            sym_records.columns = sym_opt["dim"] + [val_col]

            # insert "symbols" column
            if self._symbols_dimension:
                new_name = self._dict_get(sym_opt, "newName", sym_opt["sname"])
                sym_records.insert(loc=0, column="symbols", value=new_name)

            dataframes[self.__gt2pytypemap__[type(sym)]].append(sym_records)

            # save gt.SpecialValues.NA to recover after pd.concat
            if isinstance(sym, gt.Parameter):
                if all(
                    sym_records[val_col].isna()
                ):  # recover only if all records are NAs according to pandas
                    gt_na_values.extend(gt.SpecialValues.isNA(sym_records[val_col]))
                else:
                    gt_na_values.extend([False] * len(sym_records[val_col]))

        output_types = sorted(output_types, reverse=True)

        for ot in output_types:
            self._check_symbol_exists(self._output_name[ot])

        # save categories that might be lost after pandas.concat
        # TODO: remove when fixed by pandas: https://github.com/pandas-dev/pandas/issues/51362
        output_dim_cat_map = self._save_categories(
            unique_output_dimensions, dataframes, output_types
        )
        outputs = self._concatenate_dataframes(
            dataframes,
            output_types,
            unique_output_dimensions,
            gt_na_values,
            output_dim_cat_map,
        )

        # write outputs to database
        symbols = ["symbols"] if self._symbols_dimension else []
        for ot in output_types:
            if ot == "set":
                self._cdb.container.addSet(
                    self._output_name[ot],
                    domain=symbols + self._output_dimensions,
                    records=outputs[ot],
                )
            elif ot == "parameter":
                self._cdb.container.addParameter(
                    self._output_name[ot],
                    domain=symbols + self._output_dimensions,
                    records=outputs[ot],
                )

            if self._trace > 2:
                self._cdb.print_log(
                    f"Connect Container symbol={self._output_name[ot]}:\n {self._cdb.container[self._output_name[ot]].records}\n"
                )

        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
