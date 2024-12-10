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

class Ols (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'ols: This estimates the unknown parameters in a linear regression model.'
        self.add_posargdef('i',   'id.in:set:1',  'Name of set of observations i(*)')
        self.add_posargdef('p',   'id.in:set:1',  'Name of set of estimates p(*)')
        self.add_posargdef('A',   'id.in:par:2',  'Name of two-dimensional explanatory variable matrix A(i,p)')
        self.add_posargdef('y',   'id.in:par:1',  'Name of one-dimensional dependent variable y(i)')
        self.add_posargdef('est', 'id.out:par:1', 'Name of one-dimensional estimated statistical coefficients est(p)')
        self.add_namedargdef('gdxIn=fileIn.gdx',  'fnExist',    'Name of GDX file that contains symbols i, p, A, and y', shell_req=True)
        self.add_namedargdef('gdxOut=fileOut.gdx','fnWriteable','Name of GDX file that contains symbol est and info symbols after execution', shell_req=True)
        self.add_namedargdef('intercept=0|1|2','int','Choice for constant term\n0 - no constant term or intercept will be added to the problem\n1 - a constant term will always be added\n2 - the algorithm will add a constant term only if there is\n    no data column with all ones in the matrix A', argdefault=2)
        self.add_namedargdef('rcond=val','float','Cut-off ratio for small singular values of A used as\nargument rcond to np.linalg.lstsq', argdefault=-1.0)
        self.add_namedargdef('covar=id','id.out:par:2','Statistical info: variance-covariance matrix CoVar(p,p)')
        self.add_namedargdef('df=id','id.out:par:0','Statistical info: degrees of freedom (scalar)')
        self.add_namedargdef('fitted=id','id.out:par:1','Statistical info: fitted values for dependent variable fitted(i)')
        self.add_namedargdef('r2=id','id.out:par:0','Statistical info: R squared (scalar)')
        self.add_namedargdef('resid=id','id.out:par:1','Statistical info: residuals resid(i)')
        self.add_namedargdef('resvar=id','id.out:par:0','Statistical info: residual variance (scalar)')
        self.add_namedargdef('rss=id','id.out:par:0','Statistical info: residual sum of squares (scalar)')
        self.add_namedargdef('se=id','id.out:par:1','Statistical info: standard errors se(p)')
        self.add_namedargdef('sigma=id','id.out:par:0','Statistical info: standard error (scalar)')
        self.add_namedargdef('tval=id','id.out:par:1','Statistical info: standard errors se(p)')
        self._export = []

    def add_to_output(self, m, key, domain=None, recs=None):
        if key in self.namedargs:
            id = self.namedargs[key]
            self._export.append(id)
            if domain is None:
                m.addParameter(id, records=recs)
            else:
                m.addParameter(id, domain, records=recs)

    def execute(self):
        if self.dohelp():
            return
        import gams.transfer as gt
        import numpy as np
        self.process_args()
        i, p, A, y, est = self.posargs

        m = gt.Container(system_directory=self._system_directory)
        self.read_id_inputs(m, [i, p, A, y])

        m[A].domain = [m[i],m[p]]
        m[y].domain = [m[i]]
        a = m[A].toDense()
        Y = m[y].toDense()

        rb = None
        rcond = self.namedargs_val("rcond")
        intercept = self.namedargs_val("intercept")
        need_intercept = True if intercept in [1,2] else False
        if intercept == 2:
            for c in range(a.shape[1]):
                if np.all(a[:,c] == 1):
                    need_intercept = False
                    break
        if need_intercept:
            self._tools.print_log('Intercept added')
            rb = -1
            o = np.ones((a.shape[0], 1))
            a = np.append(a, o, axis=1)

        mm = a.shape[0]
        nn = a.shape[1]
        x, rss = np.linalg.lstsq(a, Y, rcond=rcond)[:2]
        fitted = np.matmul(a, x)
        residuals = Y - fitted
        df = mm - nn
        if df <= 0:
            self.tool_error(f'Degrees of freedom df=m-n should be >0, is {mm}-{nn}={df}', print_help=False)
        resvar = rss[0]/df
        sigma = np.sqrt(resvar)
        meanf = np.sum(fitted)/mm
        mss = np.dot(fitted-meanf, fitted-meanf)
        r2 = mss/(mss+rss[0])
  
        if 'se' in self.namedargs or 'covar' in self.namedargs or 'tval' in self.namedargs:
            try:
                MSE = (sum((Y-fitted)**2))/df
                ainv = np.linalg.inv(np.dot(a.T,a))
                var_b = MSE*(ainv.diagonal())
                if len([v for v in var_b if v < 0]):
                    self.tool_error('Unexpected negative values in var_b', print_help=False)
                se = np.sqrt(var_b)
                tval = x / se
                covar = ainv*resvar
            except Exception as e:
                self._tools.print_log(str(e))
                if not np.allclose(np.dot(np.dot(a.T,a), ainv), np.eye(ainv.shape[0])):
                    self._tools.print_log(f'Inversion of matrix failed. Condition number: {np.linalg.cond(np.dot(a.T,a))}')
                se = []
                tval = []
                covar = []
        m.addParameter(est,[m[p]], records=x[:rb])
        self._export.append(est)
        if 'covar'  in self.namedargs: self.add_to_output(m,'covar' , [m[p],m[p]], recs=covar[:rb,:rb])
        if 'df'     in self.namedargs: self.add_to_output(m,'df'    , recs=df)
        if 'fitted' in self.namedargs: self.add_to_output(m,'fitted', [m[i]], recs=fitted)
        if 'r2'     in self.namedargs: self.add_to_output(m,'r2'    , recs=r2)
        if 'resid'  in self.namedargs: self.add_to_output(m,'resid' , [m[i]], recs=residuals)
        if 'resvar' in self.namedargs: self.add_to_output(m,'resvar', recs=resvar)
        if 'rss'    in self.namedargs: self.add_to_output(m,'rss'   , recs=rss[0])
        if 'se'     in self.namedargs: self.add_to_output(m,'se'    , [m[p]], recs=se[:rb])
        if 'sigma'  in self.namedargs: self.add_to_output(m,'sigma' , recs=sigma)
        if 'tval'   in self.namedargs: self.add_to_output(m,'tval'  , [m[p]], recs=tval[:rb])

        self.write_id_outputs(m, self._export)
