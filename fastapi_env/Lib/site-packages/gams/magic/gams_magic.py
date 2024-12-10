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

from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.magic_arguments import (argument, magic_arguments, parse_argstring)
import pandas as pd

from gams.magic.interactive import GamsInteractive


@magics_class
class GamsMagic(Magics):

    def __init__(self, shell):
        # You must call the parent constructor
        super(GamsMagic, self).__init__(shell)
        self.shell.user_ns['gams'] = self
        self._gams_interactive = GamsInteractive()

    def from2dim(self, df, column_names=None):
        return self._gams_interactive.from2dim(df, column_names)

    def pivot(self, df, index=None, columns=None, values=None):
        return self._gams_interactive.pivot(df, index, columns, values)

    def pivot2d(self, df):
        return self._gams_interactive.pivot2d(df)

    def _get_write_all(self):
        return self._gams_interactive.write_all
    def _set_write_all(self, value):
        self._gams_interactive.write_all = value
    write_all = property(_get_write_all, _set_write_all)

    def _get_read_all(self):
        return self._gams_interactive.read_all
    def _set_read_all(self, value):
        self._gams_interactive.read_all = value
    read_all = property(_get_read_all, _set_read_all)    
    
    def _get_exchange_container(self):
        return self._gams_interactive.exchange_container
    exchange_container = property(_get_exchange_container)

    def _get_active_name(self):
        return self._gams_interactive.active
    active = property(_get_active_name)

    def create(self, name, activate=True):
        self._gams_interactive.create(name, activate)

    def activate(self, name):
        self._gams_interactive.activate(name)

    def _get_job_prefix(self):
        self._gams_interactive._get_job_prefix()

    def _new_job_name(self):
        self._gams_interactive._new_job_name()

    @magic_arguments()
    @argument( "--system_directory", "-s", help=("GAMS system directory"))
    @line_magic
    def gams_reset(self, line=""):
        args = parse_argstring(self.gams_reset, line)
        self.reset(args.system_directory)

    def reset(self, system_directory=None):
        self._gams_interactive.reset(system_directory)

    @line_magic
    def gams_log(self, line):
        self._gams_interactive.gams_log()

    @magic_arguments()
    @argument(
        '-e', '--execution', action='store_true'
    )
    @line_magic
    def gams_lst(self, line):
        args = parse_argstring(self.gams_lst, line)
        self._gams_interactive.gams_lst(bool(args.execution))

    @magic_arguments()
    @argument(
        '-a', '--all', action='store_true'
    )
    @argument(
        '-k', '--keep', action='store_true'
    )
    @argument(
        '-c', '--closedown', action='store_true'
    )
    @line_magic
    def gams_cleanup(self, line=""):
        args = parse_argstring(self.gams_cleanup, line)
        self._gams_interactive.gams_cleanup(args.closedown, args.all, args.keep)

    def _parse_trace_file(self, trc_file):
        return self._gams_interactivate._parse_trace_file(trc_file)

    def _get_description(self, sym):
        return self._gams_interactivate._get_description(sym)

    def _get_dom_str(self, sym):
        return self._gams_interactivate._get_dom_str(sym)

    def _get_dom(self, m, sym):
        return self._gams_interactivate._get_dom(m, sym)

    @line_cell_magic
    def gams(self, line, cell=None):
        line = line.strip()
        code = []
        if line:
            code.append(line)
        if cell:
            code.append(cell)
        code = "\n".join(code)
        return self._gams_interactive.gams(code)
