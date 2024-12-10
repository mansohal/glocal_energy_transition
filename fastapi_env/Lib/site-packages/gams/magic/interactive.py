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

from gams.control import *
from gams import transfer as gt
import pandas as pd
import os
import shutil
import glob
import uuid

class GamsInteractive(object):
    
    def __init__(self):
        self._system_directory = None
        self._envs = {}
        self._need_reset = True
        self._fprefix = 'gj_' + str(uuid.uuid4())[:8]
        self._current_env = None
        
    def from2dim(self, df, column_names=None):
        if column_names is None:
            return pd.DataFrame(df.stack()).reset_index()
        else:
            df = pd.DataFrame(df.stack()).reset_index()
            return df.rename(columns=dict(zip(df.columns, column_names)))

    def pivot(self, df, index=None, columns=None, values=None):
        df = df.pivot_table(index=index, columns=columns, values=values, fill_value=0)
        if type(index) == str:
            df.index.names = [None]
        else:
            df.index.names = [None] * len(index)
        if type(columns) == str:
            df.columns.names = [None]
        else:
            df.columns.names = [None] * len(columns)
        return df

    def pivot2d(self, df):
        return self.pivot(df, index=df.columns[0], columns=df.columns[1], values=df.columns[2])

    def _get_latest_file(self, pattern):
        return max(glob.glob(pattern), key=os.path.getmtime)
    
    def _set_write_all(self, value):
        if self._need_reset:
            self.reset()
        self._current_env._write_all = value

    def _get_write_all(self):
        if self._need_reset:
            self.reset()
        return self._current_env._write_all

    write_all = property(_get_write_all, _set_write_all)

    def _set_read_all(self, value):
        if self._need_reset:
            self.reset()
        self._current_env._read_all = value

    def _get_read_all(self):
        if self._need_reset:
            self.reset()
        return self._current_env._read_all

    read_all = property(_get_read_all, _set_read_all)
    
    def _get_exchange_container(self):
        if self._need_reset:
            self.reset()
        return self._current_env._m

    exchange_container = property(_get_exchange_container)
    
    def _get_active_name(self):
        if self._need_reset:
            self.reset()
        return self._current_env._name

    active = property(_get_active_name)
    
    def create(self, name, activate=True):
        self._envs[name] = _GamsEnvironment(self._fprefix, name, self._system_directory)
        if activate:
            self.activate(name)
            
    def activate(self, name):
        self._current_env = self._envs[name]

    def _get_job_prefix(self):
        return self._fprefix + '_' + self._current_env._name + '_'

    def _new_job_name(self):
        self._current_env._jobNumber = self._current_env._jobNumber + 1
        return self._get_job_prefix() + str(self._current_env._jobNumber)

    def reset(self, system_directory=None):
        if system_directory is None:  # keep system directory if system_directory was not provided
            pass
        elif system_directory == '':  # reset the system directory to be found automatically if the empty string is provided
            self._system_directory = None
        else:  # a system directory was provided
            self._system_directory = system_directory

        if self._current_env is None:
            self.create('base')
        else:
            self.create(self._current_env._name)
        self._need_reset = False

    def gams_reset(self, system_directory=None):
        self.reset(system_directory)

    def gams_log(self):
        if self._need_reset:
            self.reset()
        latest_log_file = self._get_latest_file(self._get_job_prefix() + '*.log')
        with open(latest_log_file) as f:
            print(f.read())

    def gams_lst(self, execution):
        if self._need_reset:
            self.reset()
        latest_lst_file = self._get_latest_file(self._get_job_prefix() + '*.lst')
        if execution:
            with open(latest_lst_file) as f:
                content = f.readlines()
                in_execution = False
                for l in content:
                    if l.startswith("E x e c u t i o n"):
                        in_execution = True
                    elif l.startswith("EXECUTION TIME"):
                        in_execution = False
                    if in_execution:
                        print(l, end="")
        else:
            with open(latest_lst_file) as f:
                print(f.read())

    def gams_cleanup(self, closedown=False, all=False, keep=False):
        if closedown:
            for k, v in self._envs.items():
                v.cleanup(keep=False)
            self._current_env = None
            self._envs = {}
            self._need_reset = True
        elif all:
            for k, v in self._envs.items():
                v.cleanup(keep=keep)
        else:
            self._current_env.cleanup(keep=keep)
        if not closedown and not keep:
            if all:
                for k, v in self._envs.items():
                    self.create(k)
            else:
                self.create(self._current_env._name)

    def _parse_trace_file(self, trc_file):
        model_stat = ["", "Optimal Global", "OptimalLocal", "Unbounded", "InfeasibleGlobal", "InfeasibleLocal",
                      "InfeasibleIntermed", "Feasible", "Integer", "NonIntegerIntermed", "IntegerInfeasible",
                      "LicenseError", "ErrorUnknown", "ErrorNoSolution", "NoSolutionReturned", "SolvedUnique",
                      "Solved", "SolvedSingular", "UnboundedNoSolution", "InfeasibleNoSolution"]
        solve_stat = ["", "Normal", "Iteration", "Resource", "Solver", "EvalError", "Capability", "License", "User",
                      "SetupErr", "SolverErr", "InternalErr", "Skipped", "SystemErr"]

        with open(trc_file, 'r') as f:
            lines = f.readlines()
            if len(lines) < 6:  # no solve in GAMS code
                return None
            header = (lines[2] + lines[3]).replace('*', '').replace('\n', '').replace(' ', '').split(',')
            used_columns = ["ModelType", "SolverName", "NumberOfEquations", "NumberOfVariables", "ModelStatus",
                            "SolverStatus", "ObjectiveValue", "SolverTime"]
            alt_col_names = ["Model Type", "Solver", "#equ", "#var", "Model Status", "Solver Status", "Objective",
                             "Solver Time"]
            data = []
            for l in lines[5:]:
                values = l.split(',')
                display_values = []
                for idx in range(len(header)):
                    if header[idx] in used_columns:
                        if header[idx] == "ModelStatus":
                            display_values.append(model_stat[int(values[idx])] + " (" + values[idx] + ")")
                        elif header[idx] == "SolverStatus":
                            display_values.append(solve_stat[int(values[idx])] + " (" + values[idx] + ")")
                        elif header[idx] == "ObjectiveValue":
                            if values[idx] != 'NA':
                                display_values.append(round(float(values[idx]), 4))
                            else:
                                display_values.append('NA')
                        else:
                            display_values.append(values[idx])

                data.append(display_values)

            df = pd.DataFrame(data, columns=alt_col_names)
            df = df[["Solver Status", "Model Status", "Objective", "#equ", "#var", "Model Type", "Solver", "Solver Time"]]
            return df
            
    def _get_description(self, sym):
        d = sym.description
        if "'" in d:
            return '"' + d + '"'
        else:
            return "'" + d + "'"

    def _get_dom_str(self, sym):
        if sym.dimension == 0:
            return ""
        else:
            dom = []
            for d in sym.domain:
                if type(d) == str:
                    dom.append('*')
                else:  # Set or Alias
                    dom.append(d.name)
            return '(' + ','.join(dom) + ')'

    def _get_dom(self, m, sym):
        dom = []
        for d in sym.domain:
            if type(d) == str:
                dom.append(d)
            else:  # Set or Alias
                dom.append(m.data[d.name])
        return dom
        
    def gams(self, code):
        if self._need_reset:
            self.reset()
        solve_summary = None
        if code:
            job_name = self._new_job_name()
            user_code_start_line = 2
            tmpcode = '$gdxIn ' + job_name + '_gdxin.gdx' + '\n$onMultiR'
            sym_list = []
            for name, sym in self._current_env._m.data.items():
                if not sym.modified and not self.write_all:
                    continue
                if type(sym) == gt.Set and sym.is_singleton:
                    tmpcode += '\n$if not declared ' + name + ' singleton set ' + name + self._get_dom_str(sym) + ' ' + self._get_description(sym) + ';'
                elif type(sym) == gt.Set:
                    tmpcode += '\n$if not declared ' + name + ' set ' + name + self._get_dom_str(sym) + ' ' + self._get_description(sym) + ';'
                elif type(sym) == gt.Parameter and sym.dimension == 0:
                    tmpcode += '\n$if not declared ' + name + ' scalar ' + name + ' ' + self._get_description(sym) + ';'
                elif type(sym) == gt.Parameter:
                    tmpcode += '\n$if not declared ' + name + ' parameter ' + name + self._get_dom_str(sym) + ' ' + self._get_description(sym) + ';'
                elif type(sym) == gt.Variable:
                    tmpcode += '\n$if not declared ' + name + ' ' + sym.type + ' variable ' + name + self._get_dom_str(sym) + ' ' + self._get_description(sym) + ';'
                elif type(sym) == gt.Equation:
                    tmpcode += '\n$if not declared ' + name + ' equation ' + name + self._get_dom_str(sym) + ' ' + self._get_description(sym) + ';'
                elif type(sym) == gt.Alias:
                    tmpcode += '\n$if not declared ' + name + ' alias (' + name + ',' + sym.alias_with.name + ');'
                else:
                    raise Exception('unknown symbol type ' + type(sym))
                user_code_start_line += 1
                if type(sym) != gt.Alias:
                    tmpcode += '\n$load ' + name
                    user_code_start_line += 1
                    sym_list.append(name)
            self._current_env._m.write(job_name + '_gdxin.gdx', sym_list)

            code = tmpcode + "\n$gdxIn\n$offeolcom\n$eolcom #\n" + code
            user_code_start_line += 3
            self._current_env.job = self._current_env._ws.add_job_from_string(code, checkpoint=self._current_env._cp, job_name=job_name)
            opt = self._current_env._ws.add_options()
            trc_file_name = job_name + ".trc"
            trc_file_path = os.path.join(self._current_env._ws.working_directory, trc_file_name)
            if os.path.isfile(trc_file_path):
                os.remove(trc_file_path)
            opt.trace = trc_file_name
            opt.traceopt = 3
            opt.gdx = job_name + '_gdxout.gdx'
            if not self.read_all:
                opt.reference = job_name + '.ref'
            with open(job_name + ".log", "w") as logFile:
                self._current_env.job.run(opt, checkpoint=self._current_env._cpnew, output=logFile, create_out_db=False)
            if os.path.exists(self._current_env._ws._working_directory + os.sep + self._current_env._cp._checkpoint_file_name):
                try:
                    os.remove(self._current_env._ws._working_directory + os.sep + self._current_env._cp._checkpoint_file_name)
                except:
                    pass
            shutil.move(self._current_env._cpnew._checkpoint_file_name, self._current_env._cp._checkpoint_file_name)

            readsyms = {}  # cannot use set because sets are unordered and copying symbols into GTP needs good order
            if not self.read_all:  # process reference file to get symbols written to by user code
                with open(job_name + '.ref', 'r') as f:
                    for l in f.readlines():
                        items = l.split()
                        if items[0] == '0':  # end of reference file code section
                            break
                        if int(items[5]) < user_code_start_line:  # our import of data, not user code
                            continue
                        if items[4] in ['declared', 'defined', 'impl-asn', 'assigned']:
                            readsyms[items[2]] = None
                if len(readsyms) == 0:
                    return None

            m_out = gt.Container(job_name + '_gdxout.gdx', system_directory=self._system_directory)
            if self.read_all:
                readsyms = m_out.data

            m = self._current_env._m
            for name in readsyms.keys():
                try:
                    sym = m_out.data[name]
                except:
                    continue  # the reference file might have model, file, acronym symbols that do not exist in GDX, so we better skip these
                gtsym = m.data.get(name, None)
                if gtsym:
                    if type(sym.records) == pd.DataFrame:
                        gtsym.setRecords(sym.records)
                        if not gtsym.isValid():
                            print(f'*** Validation on symbol {gtsym.name} failed')
                else:
                    if type(sym) == gt.Set:
                        gtsym = m.addSet(name, self._get_dom(m, sym), sym.is_singleton, None, False, sym.description)
                    elif type(sym) == gt.Parameter:
                        gtsym = m.addParameter(name, self._get_dom(m, sym), None, False, sym.description)
                    elif type(sym) == gt.Variable:
                        gtsym = m.addVariable(name, sym.type, self._get_dom(m, sym), None, False, sym.description)
                    elif type(sym) == gt.Equation:
                        gtsym = m.addEquation(name, sym.type, self._get_dom(m, sym), None, False, sym.description)
                    elif type(sym) == gt.Alias:
                        gtsym = m.addAlias(name, m.data[sym.alias_with.name])
                    else:
                        raise Exception('unknown symbol type ' + type(sym))
                    if type(sym) != gt.Alias and type(sym.records) == pd.DataFrame:
                        gtsym.setRecords(sym.records)
                        if not gtsym.isValid():
                            print(f'*** Validation on symbol {gtsym.name} failed')
            solve_summary = self._parse_trace_file(trc_file_path)
            self._current_env._m.modified = False

        return solve_summary
        
class _GamsEnvironment:
    def __init__(self, prefix, name, system_directory=None):
        self._name = name
        self._m = gt.Container(system_directory=system_directory)
        self._jobNumber = 1
        self._job = None
        self._cp = None
        self._cpnew = None
        self._ws = None
        self._prefix = prefix
        self._write_all = False
        self._read_all = False

        self._ws = GamsWorkspace(".", system_directory)
        job_name = prefix + '_' + name
        self._job = self._ws.add_job_from_string("$onMultiR\n", job_name=job_name + '_1_reset')
        self._cp = self._ws.add_checkpoint(checkpoint_name=job_name + "_cp")
        self._cpnew = self._ws.add_checkpoint(checkpoint_name=job_name + "_cpnew")
        with open(job_name + "_1.log", "w") as logFile:
            self._job.run(checkpoint=self._cp, output=logFile, create_out_db=False)

    def cleanup(self, keep=False):
        to_be_deleted = []
        for ext in ['g00', 'gdx', 'lst', 'log', 'gms', 'pf', 'trc', 'ref']:
            to_be_deleted += glob.glob(self._prefix + '_' + self._name + '_*.' + ext)
        if not keep:
            del self._job
            del self._cp
            del self._cpnew
            del self._ws
        else:
            keep_files = []
            for ext in ['g00', 'gdx', 'lst', 'log']:
                keep_files.append(self._get_latest_file(self._prefix + '_' + self._name + '_*.' + ext))
            to_be_deleted = set(to_be_deleted) - set(keep_files)

        for f in to_be_deleted:
            try:
                os.remove(f)
            except Exception as e:
                print("Warning:", e)

