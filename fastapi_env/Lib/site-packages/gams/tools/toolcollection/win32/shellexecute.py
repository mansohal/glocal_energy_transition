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

class Shellexecute (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'shellexecute: This allows to spawn an external program based on the file type of the document to open. (MS Windows only)'
        self.add_posargdef('progargs', 'str.list',   'Program and arguments')
        self.add_namedargdef('dir=workdir', 'str', 'The directory where the file to be opened is located', argdefault='.')
        self.add_namedargdef('verb=open|...', 'str', 'Action to be performed.\nThe allowed actions are application dependent.\nSome commonly available actions include\n-edit:  Launches an editor and opens the document for editing\n-find:  Initiates a search starting from the specified directory\n-open:  Launches an application. If this file is not an executable file, its associated application is launched\nprint: Prints the document file\nproperties: Displays the objects properties', argdefault='open')
        self.add_namedargdef('showCmd=0..11','int',  'Specifies how an application is to be displayed when it is opened\n The map between numerical values 0 to 11 and symbolic names can be found here:\nhttps://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow', argdefault=0)

    def execute(self):
        if self.dohelp():
            return
        if os.name != 'nt':
            self.tool_error('shellexecute only for MS Windows', print_help=False)

        self.process_args()
        pargs = self.posargs[0].split()

        import ctypes
        try:
            rc = ctypes.windll.shell32.ShellExecuteW(None, self.namedargs_val("verb"), pargs[0], ' '.join(pargs[1:]), self.namedargs_val("dir"), self.namedargs_val("showCmd"))
            if rc < 32:
                self.tool_error(ctypes.WinError())
        except Exception as e:
            self.tool_error(str(e), print_help=False)
