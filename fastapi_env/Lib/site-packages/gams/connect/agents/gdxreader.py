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
from gams.core.numpy import Gams2Numpy
import gams.transfer as gt
import pandas as pd


class GDXReader(ConnectAgent):
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
        self._symbols = inst["symbols"]
        self._gdx_file = os.path.abspath(inst["file"])
        self._trace = inst["trace"]

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")
        cdb_empty = len(self._cdb.container) == 0
        if cdb_empty:
            gdx = self._cdb.container
        else:
            gdx = gt.Container(system_directory=self._system_directory)
        if self._symbols == "all":
            gdx.read(self._gdx_file)
        else:
            sym_names = [sym["name"] for sym in self._symbols]
            gdx.read(self._gdx_file, symbols=sym_names)
            if self._trace > 1:
                self._cdb.print_log(f"GDX symbols: {gdx.listSymbols()}\n")
            # Renaming
            for sym in self._symbols:
                if sym["newName"] is not None:
                    if sym["newName"] in gdx:
                        self._connect_error(
                            f"Can not read >{sym['name']}< as >{sym['newName']}< because a symbol with this name was read already."
                        )
                    gdx.renameSymbol(sym["name"], sym["newName"])

        # For symbols with None records, empty df is assigned
        for _, sym in gdx:
            self._transform_sym_none_to_empty(sym)

        if self._trace > 0:
            self._describe_container(gdx, "GDX Container:")
        if self._trace > 2:
            for name, sym in gdx.data.items():
                self._cdb.print_log(f"GDX Container symbol={name}:\n {sym.records}\n")

        if not cdb_empty:
            # Copy from gdx to container
            self._check_symbol_exists(gdx.listSymbols())
            self._cdb.container.read(gdx)

            # Change order of '*' categories to GDX UEL order
            g2np = Gams2Numpy(self._system_directory)
            gdx_uels = {k: v for v, k in enumerate(g2np.gdxGetUelList(self._gdx_file))}
            for sym_name in gdx.listSymbols():
                sym = self._cdb.container[sym_name]
                if (
                    sym.dimension > 1
                    and not isinstance(sym, gt.Alias)
                    and isinstance(sym.records, pd.DataFrame)
                ):
                    for pos, d in enumerate(sym.domain[1:]):
                        if isinstance(d, str):
                            col = sym.records[sym.records.columns[pos + 1]]
                            cat_sorted = sorted(col.cat.categories, key=gdx_uels.get)
                            sym.records[sym.records.columns[pos + 1]] = col.astype(
                                pd.CategoricalDtype(categories=cat_sorted, ordered=True)
                            )

        if self._trace > 2:
            for name, sym in self._cdb.container.data.items():
                self._cdb.print_log(
                    f"Connect Container symbol={name}:\n {sym.records}\n"
                )
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
