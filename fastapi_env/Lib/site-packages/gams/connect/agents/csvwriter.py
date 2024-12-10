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

import os
from gams import transfer as gt
from gams.connect.agents.connectagent import ConnectAgent
import pandas as pd


class CSVWriter(ConnectAgent):

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
        inst["file"] = os.path.abspath(inst["file"])
        self._file = inst["file"]
        self._name = inst["name"]
        self._header = inst["header"]
        self._set_header = inst["setHeader"]
        self._unstack = inst["unstack"]
        self._skip_text = inst["skipText"]
        self._field_sep = inst["fieldSeparator"]
        self._decimal_sep = inst["decimalSeparator"]
        self._quoting = inst["quoting"]
        self._trace = inst["trace"]
        self._to_csv_arguments = self._dict_get(inst, "toCSVArguments", {})
        self._value_subs = self._dict_get(inst, "valueSubstitutions", {})

        if isinstance(self._unstack, list):
            self._unstack = [i - 1 for i in self._unstack]

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container:")

        if self._name not in self._cdb.container:
            self._connect_error(f"Symbol '{self._name}' not found in Connect database.")

        gt_sym = self._cdb.container[self._name]

        if self._trace > 2:
            self._cdb.print_log(
                f"Connect Container symbol={self._name}:\n {gt_sym.records}\n"
            )

        if not isinstance(gt_sym, gt.Set) and not isinstance(gt_sym, gt.Parameter):
            self._connect_error(
                f"Symbol type >{type(gt_sym)}< of symbol >{self._name}< is not supported. Supported symbol types are set and parameter."
            )

        dim = gt_sym.dimension
        df = self._sym_records_no_none(gt_sym).copy(deep=True)

        df = self._apply_value_substitutions(
            df,
            self._value_subs,
            "par" if isinstance(gt_sym, gt.Parameter) else "set",
            sv_eps="EPS",
            sv_na="NA",
            sv_undef="UNDEF",
            sv_posinf="INF",
            sv_neginf="-INF",
        )

        if dim != 0:
            df = df.set_index(list(df.columns[:dim]))
            index = True
            if self._trace > 2:
                self._cdb.print_log(f"DataFrame after .set_index():\n{df}")
        else:
            index = False

        if self._unstack and dim > 1:
            if isinstance(self._unstack, list):
                df = df.unstack(
                    level=self._unstack
                )  # unstacks and sorts remaining index
            else:
                df = df.unstack()  # unstacks and sorts remaining index
            df.columns = df.columns.droplevel()
            df.sort_index(axis="columns", inplace=True)  # sorts column indices
            if self._trace > 2:
                self._cdb.print_log(f"DataFrame after unstack:\n{df}")
            if isinstance(gt_sym, gt.Set):
                if self._skip_text:
                    # pandas-version-check
                    if hasattr(pd.DataFrame, "map"):  # pandas >= 2.1.0
                        df = df.map(lambda x: "Y" if isinstance(x, str) else x)
                    else:  # pandas < 2.1.0
                        df = df.applymap(lambda x: "Y" if isinstance(x, str) else x)
                else:
                    df = df.replace("", "Y")
        else:
            if index:
                # sort index
                df.sort_index(inplace=True)
                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame after sort:\n{df}")
            if isinstance(gt_sym, gt.Set) and self._skip_text:
                df = df.drop(columns="element_text")

        if self._set_header is not None:
            if self._trace > 1:
                self._cdb.print_log(
                    "Write header first and switch to append mode to append the DataFrame."
                )
            with open(self._file, "w") as file:
                file.write(f"{self._set_header}\n")
            to_csv_args = {"mode": "a", "header": False}
        else:
            to_csv_args = {"header": self._header}
        to_csv_args.update(
            {
                "index": index,
                "sep": f"{self._field_sep}",
                "decimal": f"{self._decimal_sep}",
                "quoting": self._quoting,
            }
        )
        to_csv_args.update(self._to_csv_arguments)

        if self._trace > 2:
            self._cdb.print_log(
                f"Final DataFrame that will be processed by pandas.to_csv:\n{df}"
            )
            self._cdb.print_log(f"pandas.to_csv arguments:\n{to_csv_args}")

        df.to_csv(self._file, **to_csv_args)
