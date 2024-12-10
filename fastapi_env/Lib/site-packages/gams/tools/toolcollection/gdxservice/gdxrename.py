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

class Gdxrename (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'gdxrename: This renames the labels in the GDX file.'
        self.add_posargdef('gdxFile',   'fnExist',    'Name of GDX file')
        self.add_posargdef('mapSet',    'id.in:set:2','Set of labels to be used for renaming mapSet(*,*)')
        self.add_namedargdef('gdxIn=fileIn.gdx', 'fnExist', 'Name of GDX file that contains map symbol "mapSet"', shell_req=True)
        self.add_namedargdef('reverse=0|1',        'int',     'Determines if mapSet with record a.b leads to a replace of\na by b or to a replace of b by a', argdefault=0)

    def execute(self):
        if self.dohelp():
            return

        import gams.transfer as gt

        self.process_args()
        gdxFile, mapSet = self.posargs
        reverse = self.namedargs_val("reverse")

        m = gt.Container(system_directory=self._system_directory)
        self.read_id_inputs(m, mapSet)

        # Make sure that mapSet is a 1-to-1 map so check for a->1 a->2 and a->1 b->1
        m1 = {}
        m2 = {}
        for rec in m[mapSet].toList():
            if reverse == 0:
                a, b  = rec[0], rec[1]
            else:
                b, a  = rec[0], rec[1]
            if m1.get(a,' ') == ' ':
                m1[a] = b
            else:
                self.tool_error(f'mapSet "{mapSet}" is multimap "{a}" to "{m1[a]}" and "{b}"', print_help=False)
            if m2.get(b,' ') == ' ':
                m2[b] = a
            else:
                self.tool_error(f'mapSet "{mapSet}" is multimap "{b}" to "{m2[b]}" and "{a}"', print_help=False)
        # Avoid a->b->c
        for a, b in m1.items():
            if not m1.get(b,' ') == ' ':
                self.tool_error(f'mapSet "{mapSet}" has chain "{a}"->"{b}"->"{m1[b]}"', print_help=False)

        # Apply map to gdxFile uels
        import gams.core.gdx as gdx
        h = gdx.new_gdxHandle_tp()
        rc , msg = gdx.gdxCreate(h, gdx.GMS_SSSIZE)
        if not rc == 1 or not len(msg) == 0:
            self.tool_error(f'Error gdxCreate: rc={rc} msg={msg}', print_help=False)

        if 0==gdx.gdxOpenAppend(h, gdxFile, 'gdxrename')[0]:
            self.tool_error(f'Error gdxOpenAppend: {gdx.gdxErrorStr(h,gdx.gdxGetLastError(h))[1]}', print_help=False)

        for a, b in m1.items():
            rc = gdx.gdxRenameUEL(h, a, b);
            if rc == -1:
                self.tool_error(f'Error gdxRenameUEL: No UelTable', print_help=False)
            elif rc in [0,2]: # everything ok, uel k does not exist
                pass
            elif rc == 3:
                self.tool_error(f'Error gdxRenameUEL: Label "{b}" exists already', print_help=False)
            else:
                self.tool_error(f'Error gdxRenameUEL: Unknown return code rc={rc}', print_help=False)

        gdx.gdxClose(h)
        gdx.gdxFree(h)
