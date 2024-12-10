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

class Exceltalk (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'exceltalk: Performs command on an Excel workbook specified by filename (MS Windows only).'
        self.add_posargdef('command', 'str', 'Recognized commands are\n               close:        Close workbook ignoring changes\n               open:         Opens workbook\n               saveAndClose: Perform save & close of the workbook')
        self.add_posargdef('excelFile', 'fnExist', 'Excel workbook filename')
        self.add_namedargdef('quit=0|1', 'int', 'Determines if Excel program should be terminated or not', argdefault=0)

    def execute(self):
        if self.dohelp():
            return
        if os.name != 'nt':
            self.tool_error('exceltalk only for MS Windows', print_help=False)

        self.process_args()
        command, excelFile = self.posargs
        quitExcel = self.namedargs_val("quit")

        try:
            import win32com.client as w3c

            xl = w3c.gencache.EnsureDispatch("Excel.Application")
        except:
            self.tool_error(f'Could not dispatch Excel', print_help=False)

        if command.lower() in ['close', 'saveandclose']:
            excelFile = os.path.basename(excelFile)
            for obj in xl.Workbooks:
                if obj.Name.lower() == excelFile.lower():
                    wb = obj
                    break
            else:
                self.tool_error(f'No workbook with name "{excelFile}" found', print_help=False)
            try:
                wb.Close(SaveChanges=command.lower() == 'saveandclose')
            except:
                self.tool_error(f'Could not close Excel workbook {excelFile}', print_help=False)
        elif command.lower() == 'open':  
            try:
                xl.Visible = True
                xl.Workbooks.Open(os.path.abspath(excelFile))
            except:
                self.tool_error(f'Could not open Excel workbook {os.path.abspath(excelFile)}', print_help=False)
        else:
            self.tool_error(f'Unknown command : "{command}"')
        if quitExcel != 0:
            xl.Quit()
