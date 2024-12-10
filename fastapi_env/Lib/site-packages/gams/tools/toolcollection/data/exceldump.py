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

from gams.tools.toolcollection.tooltemplate  import ToolTemplate
import os

class Exceldump (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'exceldump: This tool writes all worksheets of an Excel workbook to GAMS symbols.'
        self.add_posargdef('excelFile', 'fnExist',  'Excel workbook filename')
        self.add_namedargdef('gdxOut=fileOut.gdx',  'fnWriteable','Name of GDX file that contains symbols s, r, c, w, ws, vf, vs, and vu', shell_req=True)

    def execute(self):
        if self.dohelp():
            return

        self.process_args()

        from gams.connect import ConnectDatabase
        cdb = ConnectDatabase(self._tools._system_directory, ecdb=self._tools._ecdb)
        cdb.execute({'RawExcelReader': {'file': self.posargs[0], 'trace': self.namedargs_val("trace")}})

        self.write_id_outputs(cdb.container, ['s','r','c','w','ws','vf','vs','vu'])
