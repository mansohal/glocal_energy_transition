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

from abc import ABC, abstractmethod
import string
import shlex
import os
from gams.tools.errors import GamsToolsException

class ToolTemplate(ABC):
    def __init__(self, system_directory, tools):
        '''
        :param system_directory: GAMS system directory to be used.
        :param tools: An instance of gams.tools.tools.Tools.
        '''
        self._system_directory = system_directory
        self._tools = tools
        self._knowntypes = ["id.in", "id.in.list", "id.out", "id.out.list", "str", "str.list", "float", "float.list", "int", "int.list", "fnExist", "fnWriteable"]
        self._posargsdef = {}
        self._namedargsdef = {}
        self.add_namedargdef("trace=traceLevel","int","Set tracing level",0)
        self._trace = 0
        self._lastpositem = {}
        self.posargs = []
        self.namedargs = {}
        self.namedargs_list = []

    def add_posargdef(self, argid, argtype, argtext):
        if ":" in argtype:
            t = argtype.split(':')[0]
        else:
            t = argtype
        if not t in self._knowntypes:
            self.tool_error(f'Unknown argument type {t} for positional arguent {argid}')
        if self._lastpositem.get("argtype",'').endswith('.list'):
            self.tool_error(f'Cannot have additional positional arguments after entry of type list')
        self._posargsdef[argid.lower()] = {"argid":argid, "argtype":argtype, "argtext":argtext}
        self._lastpositem = self._posargsdef[argid.lower()]

    def add_namedargdef(self, argid, argtype, argtext, argdefault=None, shell_req=False, multi_occurance=False):
        if not argtype.split(':')[0] in self._knowntypes:
            self.tool_error(f'Unknown argument type {argtype} for named arguent {argid}')
        self._namedargsdef[argid.split('=')[0].lower()] = {"argid":argid, "argtype":argtype, "argtext":argtext, "argdefault":argdefault, "shell_req":shell_req, "multi_occurance":multi_occurance}

    def check_gt_sym(self, m, id, argtype):
        import gams.transfer as gt
        typemap = {gt.Set:'set', gt.Alias:'set', gt.Parameter:'par', gt.Variable:'var', gt.Equation:'equ'}
        try:
            sym = m[id]
        except:
            self.tool_error(f'Could not find symbol "{id}" in GTP container')

        ign, id_type, id_dim = argtype.split(':')
        id_dim = int(id_dim)
        if id_dim != -1 and id_dim != sym.dimension:
            self.tool_error(f'Dimension of symbols "{id}" does not match expected {id_dim}<>{sym.dimension} (actual)')
        if id_type != 'any' and typemap[type(sym)] not in id_type:
            self.tool_error(f'Unexpected type {typemap[type(sym)]} of symbol "{id}", allow is/are {id_type}')

    def convert_type(self, val, val_type='any'):
        if "." in val_type:
            v_type = val_type.split('.')[0]
        else:
            v_type = val_type
        if v_type == "int":
            try:
                return int(val)
            except:
                self.tool_error(f'Cannot convert option value "{val}" into an integer')
        elif v_type == "float":
            try:
                return float(val)
            except:
                self.tool_error(f'Cannot convert option value "{val}" into a float')
        elif v_type == "id":
            allowed = set(string.ascii_lowercase + string.ascii_uppercase + string.digits + '_')
            if not set(val) <= allowed or len(val) == 0 or val[0] == "_" or len(val) > 63:
                self.tool_error(f'String "{val}" is not a good GAMS identifier')
            return val
        elif v_type == "fnExist":
            if not (os.path.isfile(val) and os.access(val, os.R_OK)):
                self.tool_error(f'File "{val}" does not exist or cannot be read')
            return val
        else:
            return val

    def namedargs_val(self, key):
        key = key.lower()
        if key in self.namedargs:
            if self._namedargsdef[key]["multi_occurance"]:
                return [ self.namedargs_list[i][1] for i in self.namedargs[key] ]
            else:
                return self.namedargs[key]
        else:
            return self._namedargsdef[key]["argdefault"]
        
    def _check_ids(self, m, io):
        # positional arguments
        for n,ko in enumerate(self._posargsdef.items()):
            k,o = ko
            if o["argtype"].startswith(f'id.{io}'):
                self.check_gt_sym(m,self.posargs[n],o["argtype"])
        if len(self._posargsdef) < len(self.posargs) and self._lastpositem["argtype"] == f'id.{io}.list':
            for id in self.posargs[len(self._posargsdef):]:
                self.check_gt_sym(m,id,self._lastpositem["argtype"])
        # named arguments
        for k,o in self._namedargsdef.items():
            if k in self.namedargs and o["argtype"].startswith(f'id.{io}'):
                if o["multi_occurance"]:
                    for lp in self.namedargs[k]:
                        self.check_gt_sym(m,self.namedargs_list[lp][1],o["argtype"])
                else:
                    self.check_gt_sym(m,self.namedargs[k],o["argtype"])

    def check_input_ids(self, m):
        self._check_ids(m,'in')

    def check_output_ids(self, m):
        self._check_ids(m,'out')

    def process_args(self):
        numpos = 0
        argv_start = 1
        posarglist = False
        # Process positional arguments
        for s in self._tools._argv[argv_start:]:
            if posarglist: # stop when we have a named argument
                if "=" in s: break
                if s[0] == "-": break
                if s.lower() in self._namedargsdef: break
            else:
                if numpos == len(self._posargsdef):
                    break
                numpos += 1
                if ("=" in s) and ((s.split('=')[0]).lower() in self._namedargsdef):
                    self.tool_error(f'Looking for positional argument no {numpos}. Got positional argument {(s.split("=")[0]).lower()}')
                if s[0] == "-":
                    self.tool_error(f'Looking for positional argument no {numpos}. Got token ({s}) starting with "-"')
                posarglist = len(self._posargsdef) == numpos and self._lastpositem["argtype"].endswith('.list')
            arg_value = self.convert_type(s,list(self._posargsdef.items())[numpos-1][1]["argtype"])
            self.posargs.append(arg_value)
            argv_start += 1

        if not posarglist and len(self.posargs) != len(self._posargsdef):
            self.tool_error(f'Expect {len(self._posargsdef)} argument(s), got {self.posargs}.')

        # Process named arguments
        proc_value = False
        alist = self._tools._argv[argv_start:]
        while len(alist):
            if not proc_value:
                key = alist.pop(0)
                if "=" in key:
                    kv = key.split('=')
                    if len(kv) > 2:
                        self.tool_error(f'More than one "=" in argument token "{key}"')
                    key = kv[0]
                    if len(kv[1]):
                        alist.insert(0,kv[1])
                if key[0] == "-": key = key[1:]
                key = key.lower()
                if not key in self._namedargsdef:
                    #self.help()
                    self.tool_error(f'Unknown named argument "{key}"')
                if self._namedargsdef[key]["argtype"] == "None":
                    address = len(self.namedargs_list)
                    self.namedargs_list.append((key,None))
                    if self._namedargsdef[key]["multi_occurance"]:
                        if key in self.namedargs:
                            self.namedargs[key].append(address)
                        else:
                            self.namedargs[key] = [address]
                    else:
                        self.namedargs[key] = None # set or update
                    if len(alist) == 0:
                        break
                else:
                    proc_value = True
                    continue
            else: # process value
                val = alist.pop(0)
                if val == "=":
                    continue
                if val[0] == "=": val = val[1:]
                address = len(self.namedargs_list)
                if self._namedargsdef[key]["argtype"].endswith('.list'):
                    val_list = [ self.convert_type(li.strip(),self._namedargsdef[key]["argtype"]) for li in val.split(',') if len(li)]
                    self.namedargs_list.append((key,val_list))
                else:
                    self.namedargs_list.append((key,self.convert_type(val,self._namedargsdef[key]["argtype"])))
                if self._namedargsdef[key]["multi_occurance"]:
                    if key in self.namedargs:
                        self.namedargs[key].append(address)
                    else:
                        self.namedargs[key] = [address]
                else:
                    self.namedargs[key] = self.namedargs_list[-1][1] # set or update
                proc_value = False
        if proc_value:
           self.tool_error(f'Unexpected end while processing value for argument {key}') 

        if not self._tools._ecdb:
            for k,o in self._namedargsdef.items():
                if o["shell_req"] and not k in self.namedargs:
                    self.tool_error(f'Command line use requires {o["argid"]}.')
        if "trace" in self.namedargs: 
            self._trace = int(self.namedargs["trace"])
    
    def read_id_inputs(self, m, inputs):
        if 'gdxin' in self.namedargs: # get data from GDX
            try:
                m.read(self.namedargs['gdxin'], inputs)
            except Exception as e:
                self.tool_error(str(e))
        else:
            try:
                m.read(self._tools._ecdb._gmd, inputs)
            except Exception as e:
                self.tool_error(str(e))
        self.check_input_ids(m)

    def write_id_outputs(self, m, outputs):
        self.check_output_ids(m)
        if 'gdxout' in self.namedargs: # write data to GDX
            try:
                m.write(self.namedargs['gdxout'], outputs)
            except Exception as e:
                self.tool_error(str(e))
        else:
            try:
                m.write(self._tools._ecdb._gmd, outputs)
            except Exception as e:
                self.tool_error(str(e))

    def dohelp(self):
        if len(self._tools._argv) == 1 or self._tools._argv[1].lower() == "-h":
            self.help(long=False)
            return True
        elif self._tools._argv[1].lower() == "--help":
            self.help()
            return True
        else:
            return False

    def help(self, prefix='', long=True):
        self._tools.print_log(f'{prefix}{self.title}')
        usage = f"Usage: {self.title.split(':')[0]}"
        maxlen = -1
        for k,o in self._posargsdef.items():
            if len(usage) > 75:
                self._tools.print_log(f'{prefix}{usage}')
                usage = " "*len(f"Usage: {self.title.split(':')[0]}")
            usage += f' {o["argid"]}'
            maxlen = max(maxlen,len(o["argid"]))
        for k,o in self._namedargsdef.items():
            if len(usage) > 75:
                self._tools.print_log(f'{prefix}{usage}')
                usage = " "*len(f"Usage: {self.title.split(':')[0]}")
            usage += f' {o["argid"]}'
            maxlen = max(maxlen,len(o["argid"].split('=')[0]))
        self._tools.print_log(f'{prefix}{usage}')
        if long:
            for k,o in self._posargsdef.items():
                s = f'{o["argid"]}:'.ljust(maxlen+2)
                self._tools.print_log(f'{prefix}   {s} {o["argtext"]}')
            for k,o in self._namedargsdef.items():
                s = f'{o["argid"].split("=")[0]}:'.ljust(maxlen+2)
                t = o["argtext"]
                if "\n" in t:
                    pf = " "*len(f'{prefix}   {s} ')
                    if not o["argdefault"] is None:
                        t = t.replace('\n',f' (default {o["argdefault"]})\n',1)
                    t = t.replace('\n','\n'+pf)
                else:
                    if not o["argdefault"] is None:
                        t = t + f' (default {o["argdefault"]})'
                self._tools.print_log(f'{prefix}   {s} {t}')

    def tool_error(self, msg, print_help=True):
        if print_help:
            self.help(long=False)
        raise GamsToolsException(msg, error_code=1, traceback=self._trace>0)
    
    @abstractmethod
    def execute(self):
        '''
        Called by Tools. This abstract method needs to be implemented by a subclass.
        '''
        ...