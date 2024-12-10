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
from gams.connect.agents.connectagent import ConnectAgent
import gams.transfer as gt
import pandas as pd


class LabelManipulator(ConnectAgent):
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
        self._map = inst["map"]
        self._case = inst["case"]
        self._regex = inst["regex"]
        self._code = inst["code"]
        self._symbols = inst["symbols"]
        self._dimension = inst["dimension"]
        self._trace = inst["trace"]

        self._output_set = next(
            inst[key].get("outputSet")
            for key in ("code", "case", "regex", "map")
            if inst[key] is not None
        )

    def _create_output_set(self, name, map_dict):
        if name in self._cdb.container:
            self._connect_error(
                f">{name}< specified in outputSet already exists in the Connect database."
            )
        if self._trace > 1:
            self._cdb.print_log(f"Creating output set {name}")

        map_dict = {value: key for key, value in map_dict.items() if key != value}
        output_set_data = pd.DataFrame()
        output_set_data["uni"] = map_dict.keys()
        output_set_data["element_text"] = map_dict.values()
        self._cdb.container.addSet(name, records=output_set_data)

    def _get_uels_to_modify(self, sym_col):
        """
        Get UELs to modify based on the specified symbols and dimensions.

        Parameters:
            sym_col (dict): Dictionary containing symbol names as keys and dimension numbers (or 'all') as values.

        Returns:
            list: List of UELs that will be considered for modification.
        """

        # If all dimensions are specified in all symbols
        if all(value == "all" for value in sym_col.values()):
            return self._cdb.container.getUELs(list(sym_col.keys()), ignore_unused=True)

        else:
            uels_to_modify = {}
            for sym, dimension in sym_col.items():
                symbol = self._cdb.container[sym]

                if self._map and self._map["setName"] == sym:  # skip mapping set
                    continue

                uels_to_modify.update(
                    dict.fromkeys(
                        symbol.getUELs(
                            dimensions=dimension - 1 if dimension != "all" else None,
                            ignore_unused=True,
                        )
                    )
                )

            # Return unique UELS
            return uels_to_modify

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")

        sym_names = []
        sym_col = {}
        mapping_dictionary = {}

        if self._symbols == "all":
            sym_names = self._cdb.container.listSymbols()
            sym_col = {key: self._dimension for key in sym_names}

        else:
            for sym in self._symbols:
                if sym["name"] not in self._cdb.container:
                    self._connect_error(
                        f">{sym['name']}< does not exist in the Connect database."
                    )

                if sym["newName"] is not None:
                    # Creating a new symbol in the Connect database if newName is provided

                    # If newName already exists
                    self._check_symbol_exists(sym["newName"])

                    gt_symbol = self._cdb.container[sym["name"]]
                    if isinstance(gt_symbol, gt.Set):
                        gt.Set(
                            self._cdb.container,
                            sym["newName"],
                            gt_symbol.domain,
                            records=gt_symbol.records,
                        )
                    elif isinstance(gt_symbol, gt.Parameter):
                        gt.Parameter(
                            self._cdb.container,
                            sym["newName"],
                            gt_symbol.domain,
                            records=gt_symbol.records,
                        )
                    elif isinstance(gt_symbol, gt.Variable):
                        gt.Variable(
                            self._cdb.container,
                            sym["newName"],
                            gt_symbol.domain,
                            records=gt_symbol.records,
                        )
                    elif isinstance(gt_symbol, gt.Equation):
                        gt.Equation(
                            self._cdb.container,
                            sym["newName"],
                            gt_symbol.domain,
                            records=gt_symbol.records,
                        )
                    else:
                        self._connect_error("Data type not supported.")

                    sym_names.append(sym["newName"])

                else:
                    sym_names.append(sym["name"])

                sym_col[sym_names[-1]] = self._dict_get(
                    sym, "dimension", self._dimension
                )

        for sym, dimension in sym_col.items():
            symbol = self._cdb.container[sym]

            # Check if the specified dimension is valid
            if dimension != "all":
                if self._map and self._map["setName"] == sym:  # skip mapping set
                    continue
                if symbol.dimension < dimension:
                    self._connect_error(
                        f"Symbol >{sym}< has >{symbol.dimension}< dimension(s) but the specified dimension is >{dimension}<."
                    )

            # For symbols with None records, empty df is assigned
            self._transform_sym_none_to_empty(symbol)

        uels_to_modify = self._get_uels_to_modify(sym_col)

        if self._trace > 2:
            for name, sym in self._cdb.container.data.items():
                self._cdb.print_log(
                    f"Connect Container symbol={name}:\n {sym.records}\n"
                )

        # mapping functionality using a GAMS set
        if self._map:
            set_name = self._map["setName"]
            invert = self._map["invert"]

            if set_name not in self._cdb.container:
                self._connect_error(
                    f"The mapping set >{set_name}< does not exist in the Connect database."
                )

            if not isinstance(self._cdb.container[set_name], gt.Set):
                self._connect_error(f"The mapping set >{set_name}< is not a set.")

            if (
                self._cdb.container[set_name].records is None
                or self._cdb.container[set_name].records.empty
            ):
                self._connect_error(
                    f"The mapping set >{set_name}< is empty. Please fill it with the mapping."
                )
            if self._cdb.container[set_name].dimension != 1:
                self._connect_error(
                    f"The mapping set >{set_name}< should be 1-dimensional."
                )

            mapping_df = self._cdb.container[set_name].records
            if invert:
                mapping_df = mapping_df[mapping_df.columns[::-1]]
                mapping_df.columns = ["uni", "element_text"]

            mapping_dictionary = mapping_df.set_index("uni").to_dict()["element_text"]
            if self._symbols == "all":
                sym_names.remove(set_name)
                sym_col.pop(set_name)

            if self._trace > 1:
                self._cdb.print_log(
                    f'Applying map mode for symbols >{", ".join(sym_names)}<.\n'
                )
            if self._trace > 2:
                for from_uel, to_uel in mapping_dictionary.items():
                    self._cdb.print_log(f"{from_uel}  -->  {to_uel}\n")

        # casing functionality: to change the casing of labels
        elif self._case:
            rule = self._case["rule"]
            mapping_dictionary = {
                label: getattr(label, rule)() for label in uels_to_modify
            }
            if self._trace > 1:
                self._cdb.print_log(
                    f'Applying case mode for symbols >{", ".join(sym_names)}<.\n'
                )
            if self._trace > 2:
                for from_uel, to_uel in mapping_dictionary.items():
                    self._cdb.print_log(f"{from_uel}  -->  {to_uel}\n")

        # regex functionality: manipulate labels through a regex expression
        elif self._regex:
            pattern = self._regex["pattern"]
            replace = self._regex["replace"]
            mapping_dictionary = {
                label: re.sub(pattern, replace, label) for label in uels_to_modify
            }
            if self._trace > 1:
                self._cdb.print_log(
                    f'Applying regex mode for symbols >{", ".join(sym_names)}<.\n'
                )
            if self._trace > 2:
                for from_uel, to_uel in mapping_dictionary.items():
                    self._cdb.print_log(f"{from_uel}  -->  {to_uel}\n")

        # code functionality: manipulate labels through a Python expression
        elif self._code:
            rule = self._code["rule"]
            rule_id = self._code["ruleIdentifier"]
            mapping_dictionary = {
                label: eval(rule, {rule_id: label}) for label in uels_to_modify
            }
            if self._trace > 1:
                self._cdb.print_log(
                    f'Applying code mode for symbols >{", ".join(sym_names)}<.\n'
                )
            if self._trace > 2:
                for from_uel, to_uel in mapping_dictionary.items():
                    self._cdb.print_log(f"{from_uel}  -->  {to_uel}\n")

        # Apply manipulations on 'all' dimensions
        self._cdb.container.renameUELs(
            mapping_dictionary,
            [k for k, v in sym_col.items() if v == "all"],
            allow_merge=True,
        )

        # Apply manipulations on specific dimensions
        for sym_name, dimension in {
            k: v for k, v in sym_col.items() if v != "all"
        }.items():
            symbol = self._cdb.container[sym_name]
            symbol.renameUELs(
                mapping_dictionary, dimensions=dimension - 1, allow_merge=True
            )

        if self._output_set:
            self._create_output_set(self._output_set, mapping_dictionary)

        if self._trace > 2:
            for name, sym in self._cdb.container.data.items():
                self._cdb.print_log(
                    f"Connect Container symbol={name}:\n {sym.records}\n"
                )
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
