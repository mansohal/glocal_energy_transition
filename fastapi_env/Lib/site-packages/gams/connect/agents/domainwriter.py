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
from gams import transfer as gt
from gams.connect.agents.connectagent import ConnectAgent
import pandas as pd


class DomainWriter(ConnectAgent):

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
        self._drop_domain_violations = inst["dropDomainViolations"]
        self._trace = inst["trace"]
        self._write_all = self._symbols == "all"

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")
        if self._trace > 2:
            for name, sym in self._cdb.container.data.items():
                self._cdb.print_log(
                    f"Connect Container symbol={name}:\n {sym.records}\n"
                )
        if self._write_all:
            # For symbols with None records, empty df is assigned
            for _, sym in self._cdb.container:
                self._transform_sym_none_to_empty(sym)

            # Apply dropDomainViolations to all symbols
            if self._drop_domain_violations is not False:
                self._cdb.container.dropDomainViolations()

        else:
            for sym in self._symbols:
                sym_raw = sym.copy()
                self._update_sym_inst(sym, self._inst)

                if self._trace > 0:
                    self._log_instructions(
                        sym, sym_raw, description=f"Apply on symbol >{sym['name']}<:"
                    )
                regex = (
                    r'(?P<name>[a-zA-Z0-9_]+)(\((?P<domains>[a-zA-Z0-9_,"\s\']*)\))?'
                )
                ms = re.fullmatch(regex, sym["name"])

                if ms is None:
                    self._connect_error(
                        f'Invalid symbol name: >{sym["name"]}<  Hint: Only alphanumeric characters and underscores are allowed.'
                    )

                sname = ms.group("name")

                if sname not in self._cdb.container:
                    self._connect_error(
                        f"Symbol '{sname}' not found in Connect database."
                    )
                ssym = self._cdb.container[sname]

                if (
                    ms.group("domains") is not None
                ):  # domains have been specified, e.g. "a(d1, d2)", "a(d1, )", or "a()"
                    sdom = [dom.strip() for dom in ms.group("domains").split(",")]
                else:  # no domains have been specified, e.g. "a"
                    sdom = []

                # For symbols with None records, empty df is assigned
                self._transform_sym_none_to_empty(ssym)

                ddv = sym["dropDomainViolations"]
                if ddv in ["before", True]:
                    ssym.dropDomainViolations()
                if len(sdom) != len(ssym.domain):
                    self._connect_error(
                        f"Number of specified dimensions of symbol >{sym['name']}< does not correspond to the symbol's number of dimensions in the database ({len(sdom)}<>{ssym.dimension})."
                    )
                elif len(sdom) > 0:
                    new_domain = []
                    for d in sdom:
                        if d.startswith(('"', "'")):
                            if (
                                " " in d
                            ):  # Is there a space in the relaxed domain?  e.g. "a(' d 1')"
                                self._connect_error(
                                    f"Domain sets cannot contain spaces >{d}<"
                                )
                            new_domain.append(d[1:-1])

                        elif d == "":  # Empty domain
                            new_domain.append("")

                        else:
                            if d not in self._cdb.container:
                                self._connect_error(
                                    f"Domain set '{d}' not found in Connect database."
                                )
                            dsym = self._cdb.container[d]
                            assert (
                                type(dsym) in [gt.Set, gt.Alias] and dsym.dimension == 1
                            )
                            new_domain.append(dsym)
                    if self._trace > 1:
                        self._cdb.print_log(f"New domain for {sname}: {new_domain}\n")
                    ssym.domain = new_domain
                    ssym.domain_labels = ssym.domain_names
                    if ddv in ["after", True]:
                        ssym.dropDomainViolations()

        if self._trace > 2:
            for name, sym in self._cdb.container.data.items():
                self._cdb.print_log(
                    f"Connect Container symbol={name}:\n {sym.records}\n"
                )

        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
