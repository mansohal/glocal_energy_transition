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
from gams.connect.agents.connectagent import ConnectAgent
import gams.transfer as gt
import pandas as pd


class GDXWriter(ConnectAgent):

    def __init__(self, cdb, inst):
        super().__init__(cdb, inst)
        inst_raw = inst
        inst = self._normalize_instructions(inst)
        self._parse_options(inst)
        self._inst = inst
        if self._trace > 0:
            self._log_instructions(inst, inst_raw)
        if self._trace > 3:
            pd.set_option("display.max_rows", None, "display.max_columns", None)

    def _parse_options(self, inst):
        self._symbols = inst["symbols"]
        self._duplicate_records = inst["duplicateRecords"]
        inst["file"] = os.path.abspath(inst["file"])
        self._gdx_file = inst["file"]
        self._trace = inst["trace"]
        self._write_all = self._symbols == "all"

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container:")
        drmap = {"none": False, "first": "first", "last": "last"}
        write_container = self._cdb.container
        if self._write_all:
            if self._trace > 2:
                for name, sym in write_container.data.items():
                    self._cdb.print_log(
                        f"Connect Container symbol={name}:\n {sym.records}\n"
                    )
            if self._duplicate_records != "all":
                # copy Connect container to avoid altering the Connect database
                write_container = gt.Container(
                    self._cdb.container, system_directory=self._system_directory
                )
                write_container.dropDuplicateRecords(
                    keep=drmap[self._duplicate_records]
                )
            if not write_container.hasDuplicateRecords():
                write_container.write(self._gdx_file, eps_to_zero=False)
            else:
                dup_name_list = [
                    name
                    for name, sym in write_container.data.items()
                    if sym.hasDuplicateRecords()
                ]
                self._connect_error(
                    f"Following symbols have duplicate records: {dup_name_list}. Consider setting 'duplicateRecords' to 'first', 'last', or 'none'."
                )
        else:
            symbols_raw = self._symbols.copy()
            for s in self._symbols:
                self._update_sym_inst(s, self._inst)

            # Since we can't copy invalid symbols (=symbols with duplicates) we need to resolve the duplicates in the Connect container
            all_dr = any(sym["duplicateRecords"] != "all" for sym in self._symbols)
            if all_dr:
                # copy Connect container to avoid altering the Connect database
                write_container = gt.Container(
                    self._cdb.container, system_directory=self._system_directory
                )

            sym_names = []
            for sym, sym_raw in zip(self._symbols, symbols_raw):
                if self._trace > 0:
                    self._log_instructions(
                        sym, sym_raw, description=f"Write symbol >{sym['name']}<:"
                    )

                sym_name = sym["name"]
                if sym_name not in self._cdb.container:
                    self._connect_error(
                        f"Symbol >{sym_name}< not found in Connect database."
                    )

                if sym["duplicateRecords"] != "all":
                    write_container[sym_name].dropDuplicateRecords(
                        keep=drmap[sym["duplicateRecords"]]
                    )
                if not write_container[sym_name].hasDuplicateRecords():
                    sym_names.append(sym_name)
                else:
                    self._connect_error(
                        f"Symbol '{sym_name}' has duplicate records. Consider setting 'duplicateRecords' to 'first', 'last', or 'none'."
                    )
            gdx = gt.Container(system_directory=self._system_directory)
            gdx.read(write_container, sym_names)

            # Apply original categories of * domains in new Container
            for sym_name in gdx.listSymbols():
                ssym = write_container[sym_name]
                tsym = gdx[sym_name]
                if ssym.records is None:
                    continue
                for d, tdl, sdl in zip(
                    tsym.domain, tsym.domain_labels, ssym.domain_labels
                ):
                    if isinstance(d, str):
                        tsym.records[tdl] = tsym.records[tdl].astype(
                            pd.CategoricalDtype(
                                categories=ssym.records[sdl].cat.categories,
                                ordered=True,
                            )
                        )

            # Renaming
            if self._trace > 1:
                self._cdb.print_log(f"GDX symbols: {gdx.listSymbols()}\n")
            for sym in self._symbols:
                if sym["newName"] is not None:
                    gdx.renameSymbol(sym["name"], sym["newName"])

            if self._trace > 0:
                self._describe_container(gdx, "GDX Container:")
            if self._trace > 2:
                for name, sym in gdx.data.items():
                    self._cdb.print_log(
                        f"GDX Container symbol={name}:\n {sym.records}\n"
                    )
                    self._cdb.print_log(f"  Valid: {sym.isValid(verbose=True)}\n")
            gdx.write(self._gdx_file, eps_to_zero=False)
