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

class Cholesky (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'cholesky: This calculates the Cholesky decomposition of a symmetric positive definite matrix A = LL^t.'
        self.add_posargdef('i',   'id.in:set:1',  'Name of set used in matrix i(*)')
        self.add_posargdef('A',   'id.in:par:2',  'Name of two-dimensional matrix parameter A(i,i)')
        self.add_posargdef('L',   'id.out:par:2', 'Name of two-dimensional parameter containing the factor L(i,i)')
        self.add_namedargdef('gdxIn=fileIn.gdx',  'fnExist',    'Name of GDX file that contains symbols i and A', shell_req=True)
        self.add_namedargdef('gdxOut=fileOut.gdx','fnWriteable','Name of GDX file that contains symbol L after execution', shell_req=True)

    def execute(self):
        if self.dohelp():
            return

        import gams.transfer as gt
        import numpy as np

        self.process_args()
        i, A, L = self.posargs

        m = gt.Container(system_directory=self._system_directory)
        self.read_id_inputs(m, [i, A])

        m[A].domain = [m[i],m[i]]
        l = np.linalg.cholesky(m[A].toDense())
        m.addParameter(L,[m[i],m[i]], records=l)
        self.write_id_outputs(m, L)
