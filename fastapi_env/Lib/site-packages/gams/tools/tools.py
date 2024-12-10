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
import sys
import importlib
from gams.tools.errors import GamsToolsException

class Tools(object):
    def __init__(self, system_directory, ecdb=None, argv=[]):
        self._system_directory = system_directory
        self._ecdb = ecdb
        self._argv = argv


    def print_log(self, msg):
        if self._ecdb:
            self._ecdb.printLog(msg)
        else:
            print(msg)
            sys.stdout.flush()

    def all_tools(self):
        from pkgutil import iter_modules
        import importlib
        import gams.tools.toolcollection as gtc
        d = {}
        for mod in iter_modules(gtc.__path__):
            if mod.name != 'tooltemplate':
                d[mod.name] = [m.name for m in iter_modules(importlib.import_module(gtc.__package__ + "." + mod.name).__path__)]
        return d

    def help(self, tc, category='', long=True):
        if len(category):
            self.print_log(f'List of tools in {category}:')
            cats = [category]
        else:
            self.print_log('List of tools:')
            cats = list(tc.keys())
        for cat in cats:            
            if not len(category):
                self.print_log(f'  {cat}:')
            for tool in tc[cat]:
                try:
                    mod = importlib.import_module(f"gams.tools.toolcollection.{cat}.{tool}")
                except ModuleNotFoundError as e:
                    if e.name != "gams.tools.toolcollection.{cat}.{tool}": # the tool module itself was found but an import in the source itself did fail
                        raise e
                    mod = importlib.import_module(tool)
                task_class = vars(mod)[tool.capitalize()]
                task_instance = task_class(self._system_directory, self)
                task_instance.help(prefix='    ', long=long)

    def exec_tool(self):
        tc = self.all_tools()
        if len(self._argv) == 0 or self._argv[0] == '-h':
            self.help(tc, long=False)
            return
        if len(self._argv) == 0 or self._argv[0] == '--help':
            self.help(tc)
            return
        ct = self._argv[0]
        if '.' in ct:
            cat, tool = [ s.lower() for s in ct.split('.') ]
        else:
            tool = ct.lower()
            cat = []
            for c,tl in tc.items():
                if tool in tl:
                    cat.append(c)
            if len(cat) == 0: # could be cat -h
                if tool in tc and (len(self._argv) == 1 or self._argv[1] == '-h'):
                    self.help(tc, category=tool, long=False)
                    return
                if tool in tc and (len(self._argv) == 1 or self._argv[1] == '--help'):
                    self.help(tc, category=tool)
                    return
                raise GamsToolsException(f'No tool {tool} found.', error_code=2, traceback=False)
            if len(cat) > 1:
                raise GamsToolsException(f'Tool {tool} found in following categories: {cat}. Use e.g. {cat[0]}.{tool} to select specific tool.', error_code=2, traceback=False)
            cat = cat[0]
        try:
            mod = importlib.import_module(f"gams.tools.toolcollection.{cat}.{tool}")
        except ModuleNotFoundError as e:
            if e.name != "gams.tools.toolcollection.{cat}.{tool}": # the tool module itself was found but an import in the source itself did fail
                raise GamsToolsException(str(e), error_code=2, traceback=False)
            mod = importlib.import_module(tool)
        task_class = vars(mod)[tool.capitalize()]
        task_instance = task_class(self._system_directory, self)
        task_instance.execute()
            
    def _get_ecdb(self):
        return self._ecdb
    ecdb = property(_get_ecdb)
