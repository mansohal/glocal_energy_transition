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
from ctypes import *

class Gdxencoding (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'gdxencoding: This converts the unique elements in the GDX file from one encoding to another one.'
        self.add_posargdef('gdxFile',   'fnExist',    'Name of GDX file')
        self.add_namedargdef('encodingIn=codingIn',    'str',         'Input encoding of GDX string', argdefault='latin_1')
        self.add_namedargdef('encodingOut=codingOut',  'str',         'Output encoding of GDX string', argdefault='utf_8')
        self.add_namedargdef('numConv=id',             'id.out:par:0','GAMS scalar symbol to store the number of actual conversions')
        self.add_namedargdef('gdxOut=fileOut.gdx',     'fnWriteable', 'Name of GDX file that contains symbol numConv after execution')

    def _get_last_gdx_error(self, gdx_handle, gdx):
        from gams.core.gdx import GMS_SSSIZE
        error_nr = gdx.c__gdxgetlasterror(gdx_handle)
        error_msg = create_string_buffer(GMS_SSSIZE)
        gdx.c__gdxerrorstr(gdx_handle, error_nr, error_msg)
        return error_msg.value.decode('utf-8')

    def execute(self):
        if self.dohelp():
            return

        self.process_args()
        gdxFile = self.posargs[0]
        encodeIn = self.namedargs_val("encodingIn")
        encodeOut = self.namedargs_val("encodingOut")

        if self._tools._ecdb is None and 'numconv' in self.namedargs and not 'gdxout' in self.namedargs:
            self.tool_error('Command line use requires gdxOut=<fileOut.gdx> if numConv=id is set')

        import os
        import sys

        if sys.platform in ["linux", "linux2"]:
            so_name = "libgdxcclib64.so"
        elif sys.platform == "darwin":
            so_name = "libgdxcclib64.dylib"
        elif sys.platform == "win32":
            so_name = "gdxcclib64.dll"
        else:
            raise Exception(f'unknown OS {sys.platform}')
        gdx = cdll.LoadLibrary(os.path.join(self._tools._system_directory, so_name))

        gdx_handle = c_void_p()
        gdx.xcreate(byref(gdx_handle))
        ival = c_int()
        ival_p = byref(ival)

        rc = gdx.c__gdxopenappend(gdx_handle, c_char_p(gdxFile.encode()), c_char_p(f'gdxService gdxEncoding {encodeIn} -> {encodeOut}'.encode()), ival_p)
        if not rc == 1:
            self.tool_error(f'Error gdxOpenAppend: {self._get_last_gdx_error(gdx_handle, gdx)}', print_help=False)

        uel_nr = 1
        num_conv = 0
        uel = create_string_buffer(gdx.c__gdxuelmaxlength(gdx_handle)+1)
        while True:
            rc = gdx.c__gdxumuelget(gdx_handle, c_int(uel_nr), uel, ival_p)
            if rc != 1: break
            uel_out = uel.value.decode(encodeIn).encode(encodeOut)
            if uel_out != uel.value:
                if self._trace > 0:
                    self._tools.print_log(f'Converted {uel.value} to {uel_out}')
                rc = gdx.c__gdxrenameuel(gdx_handle, uel.value, uel_out)
                if not rc == 0:
                    self.tool_error(f'Error gdxRenameUEL: {self._get_last_gdx_error(gdx_handle, gdx)}', print_help=False)
                num_conv += 1
            uel_nr += 1
        gdx.c__gdxclose(gdx_handle)
        gdx.xfree(byref(gdx_handle))

        if 'numconv' in self.namedargs:
            import gams.transfer as gt

            m = gt.Container(system_directory=self._system_directory)
            m.addParameter(self.namedargs_val("numconv"), records=num_conv)
            self.write_id_outputs(m, self.namedargs_val("numconv"))
