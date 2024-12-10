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

class Excelmerge (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'excelmerge: Merges the sheets of the source Excel workbook into the destination workbook (MS Windows only).'
        self.add_posargdef('sourceExcelFile', 'fnExist',  'Source Excel workbook filename')
        self.add_posargdef('targetExcelFile', 'str',      'Merged Excel workbook filename')

    def execute(self):
        if self.dohelp():
            return
        if os.name != 'nt':
            self.tool_error('excelmerge only for MS Windows', print_help=False)

        self.process_args()
        sourceName, targetName = self.posargs

        try:
            import win32com.client as w3c

            xl = w3c.gencache.EnsureDispatch("Excel.Application")
        except:
            self.tool_error(f'Could not dispatch Excel', print_help=False)

        if not os.path.isabs(targetName):
            targetName = os.path.join(os.getcwd(), targetName)
        if not os.path.isabs(sourceName):
            sourceName = os.path.join(os.getcwd(), sourceName)

        try:
            target = xl.Workbooks.Open(Filename=targetName)
        except:
            self.tool_error(f'Could not open target Excel workbook "{targetName}"', print_help=False)

        target_sheetnames = {sheet.Name: i for i, sheet in enumerate(target.Sheets)}

        # required to overide the delete prompt shown by MS-Excel
        xl.DisplayAlerts = False

        try:
            source_sheets = xl.Workbooks.Open(Filename=sourceName).Sheets
        except:
            self.tool_error(f'Could not extract sheets from Excel workbook "{sourceName}"', print_help=False)

        for sheet in source_sheets:
            if not sheet.Name in target_sheetnames.keys():
                sheet.Copy(Before=None, After=target.Worksheets(target.Sheets.Count)) # append at the end
            else:
                # if only one sheet exists in dest add a temporary sheet so workbook is never empty
                if target.Sheets.Count == 1:
                    add_dummy_sheet = target.Sheets.Add(Before = None , After = target.Sheets(1))
                    target.Worksheets(sheet.Name).Delete()
                    sheet.Copy(Before=target.Worksheets(1))
                    add_dummy_sheet.Delete()
                else:
                    target.Worksheets(sheet.Name).Delete()
                    if target_sheetnames[sheet.Name] == 0:
                        sheet.Copy(Before=target.Worksheets(1))
                    else:
                        sheet.Copy(Before=None, After=target.Worksheets(target_sheetnames[sheet.Name]))
        try:
            target.Close(SaveChanges=True)
            xl.Quit()
        except:
            self.tool_error(f'Could not save and close Excel workbook "{targetName}"', print_help=False)
