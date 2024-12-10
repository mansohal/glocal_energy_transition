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
import pandas as pd
from gams import transfer as gt
from gams.connect.agents.connectagent import ConnectAgent


class Filter(ConnectAgent):

    def __init__(self, cdb, inst):
        super().__init__(cdb, inst)
        inst_raw = inst
        inst = self._normalize_instructions(inst)
        self._parse_options(inst)
        if self._trace > 0:
            self._log_instructions(inst, inst_raw)
        if self._trace > 3:
            pd.set_option("display.max_rows", None, "display.max_columns", None)

        self._label_filters_dict = {}
        for f in self._label_filters:
            c = f["dimension"]
            if c != "all":
                c = c - 1
            if c in self._label_filters_dict:
                self._connect_error(f"More than one filter for dimension {c+1}.")
            self._label_filters_dict[c] = f

    def _parse_options(self, inst):
        self._name = inst["name"]
        self._new_name = inst["newName"]
        self._value_filters = self._dict_get(inst, "valueFilters", [])
        self._label_filters = self._dict_get(inst, "labelFilters", [])
        self._trace = inst["trace"]

    def _filter_labels(self, df, f, c):
        if c == "all":
            for c in range(0, self._sym.dimension):
                df = self._filter_labels(df, f, c)
        else:
            if c >= self._sym.dimension:
                self._connect_error(
                    f"Invalid dimension {c+1} for symbol with {self._sym.dimension} dimensions. Hint: dimension is 1-indexed."
                )
            if f.get("keep") is not None:
                df = df.loc[df.iloc[:, c].isin(f["keep"])]
            elif f.get("reject") is not None:
                df = df.loc[~df.iloc[:, c].isin(f["reject"])]
            elif f.get("regex") is not None:
                regex = re.compile(f["regex"])
                df = df.loc[df.iloc[:, c].str.fullmatch(regex)]
        return df

    def _filter_values(self, df, f, c, skip_trace=False):
        if isinstance(self._sym, gt.Set):
            self._connect_error(
                "Value filters are not supported for symbols of type set."
            )
        rule_identifier = f["ruleIdentifier"]
        rule = self._dict_get(f, "rule", "")
        rule = (
            "(" + rule.replace(rule_identifier, f'df["{c}"]') + ")"
            if rule
            else "[True]*len(df)"
        )

        include_sv = ""
        exclude_sv = ""
        reject_sv = self._dict_get(f, "rejectSpecialValues", [])
        if isinstance(reject_sv, str):
            reject_sv = [reject_sv]

        if "EPS" in reject_sv:
            exclude_sv += f' & (~gt.SpecialValues.isEps(df["{c}"]))'
        else:
            include_sv += f' | (gt.SpecialValues.isEps(df["{c}"]))'
        if "INF" in reject_sv:
            exclude_sv += f' & (~gt.SpecialValues.isPosInf(df["{c}"]))'
        else:
            include_sv += f' | (gt.SpecialValues.isPosInf(df["{c}"]))'
        if "-INF" in reject_sv:
            exclude_sv += f' & (~gt.SpecialValues.isNegInf(df["{c}"]))'
        else:
            include_sv += f' | (gt.SpecialValues.isNegInf(df["{c}"]))'
        if "UNDEF" in reject_sv:
            exclude_sv += f' & (~gt.SpecialValues.isUndef(df["{c}"]))'
        else:
            include_sv += f' | (gt.SpecialValues.isUndef(df["{c}"]))'
        if "NA" in reject_sv:
            exclude_sv += f' & (~gt.SpecialValues.isNA(df["{c}"]))'
        else:
            include_sv += f' | (gt.SpecialValues.isNA(df["{c}"]))'
        rule += exclude_sv + include_sv

        if self._trace > 1 and not skip_trace:
            self._cdb.print_log(f'Applying rule for attribute "{c}": {rule}')
        if c == "all":
            if isinstance(self._sym, gt.Parameter):
                value_columns = ["value"]
            elif isinstance(self._sym, (gt.Variable, gt.Equation)):
                value_columns = [
                    "level",
                    "marginal",
                    "lower",
                    "upper",
                    "scale",
                ]
            for c in value_columns:
                df = self._filter_values(df, f, c, True)
        else:
            df = eval(f"df.loc[({rule})]", {"df": df, "gt": gt})
        return df

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")
        if self._name not in self._cdb.container:
            self._connect_error(f"Symbol '{self._name}' not found in Connect database.")
        self._sym = self._cdb.container[self._name]

        if self._new_name.casefold() == self._name.casefold():
            self._connect_error(
                f"newName >{self._new_name}< must be different from name >{self._name}<. Hint: The names are case-insensitive."
            )

        self._check_symbol_exists(self._new_name)

        if isinstance(self._sym, gt.Set):
            tsym = gt.Set(self._cdb.container, self._new_name, self._sym.domain)
        elif isinstance(self._sym, gt.Parameter):
            tsym = gt.Parameter(self._cdb.container, self._new_name, self._sym.domain)
        elif isinstance(self._sym, gt.Variable):
            tsym = gt.Variable(
                self._cdb.container,
                self._new_name,
                self._sym.type,
                self._sym.domain,
            )
        elif isinstance(self._sym, gt.Equation):
            tsym = gt.Equation(
                self._cdb.container,
                self._new_name,
                self._sym.type,
                self._sym.domain,
            )
        else:
            self._connect_error("Data type not supported.")

        df = self._sym_records_no_none(self._sym).copy(deep=True)

        if self._trace > 2:
            self._cdb.print_log(f"Original DataFrame:\n{df}")
        for c in self._label_filters_dict:
            f = self._label_filters_dict[c]
            if self._trace > 0:
                self._log_instructions(f, description="Applying label filter:")
            if c == "all":
                df = self._filter_labels(df, f, c)
                if self._trace > 2:
                    self._cdb.print_log(
                        f"DataFrame after label filter for dimension 'all':\n{df}"
                    )
            else:
                df = self._filter_labels(df, f, c)
                if self._trace > 2:
                    self._cdb.print_log(
                        f"DataFrame after label filter for dimension {c+1}:\n{df}"
                    )

        val_cols = [f["attribute"] for f in self._value_filters]
        if len(val_cols) != len(set(val_cols)):
            for c in set(val_cols):
                val_cols.remove(c)
            self._connect_error(
                f"More than one value filter for attribute {set(val_cols)}."
            )

        for f in self._value_filters:
            c = f["attribute"]
            if self._trace > 0:
                self._log_instructions(f, description="Applying value filter:")
            if isinstance(self._sym, gt.Parameter) and c not in ["all", "value"]:
                self._connect_error(
                    f"Invalid attribute >{c}< for symbol type parameter."
                )
            if (
                isinstance(self._sym, gt.Variable) or isinstance(self._sym, gt.Equation)
            ) and c not in ["all", "level", "marginal", "upper", "lower", "scale"]:
                self._connect_error(
                    f"Invalid attribute >{c}< for symbol type variable/equation."
                )
            df = self._filter_values(df, f, c)
            if self._trace > 2:
                self._cdb.print_log(
                    f'DataFrame after value filter for attribute "{c}":\n{df}'
                )
        tsym.setRecords(df)

        if self._trace > 2:
            self._cdb.print_log(
                f"Connect Container symbol={self._new_name}:\n {tsym.records}\n"
            )
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
