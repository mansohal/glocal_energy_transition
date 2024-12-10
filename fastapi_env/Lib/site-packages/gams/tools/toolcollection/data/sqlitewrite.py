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

from gams.tools.toolcollection.tooltemplate import ToolTemplate


class Sqlitewrite(ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = "sqlitewrite: This tool writes data from a gdx file to a sqlite database file(.db)"
        self.add_namedargdef(
            "gdxIn=<gdx_filename>",
            "fnExist",
            "Specify the input file",
            shell_req=True,
        )
        self.add_namedargdef(
            "o=<sqlite_filename>",
            "str",
            "Specify the output sqlite file",
        )
        self.add_namedargdef(
            "ids=<string>",
            "str",
            "Specify the symbols to be read separated by commas.",
            argdefault=False,
        )
        self.add_namedargdef(
            "expltext=<Y/N>",
            "str",
            "Specify if the explanatory text for set elements are also exported to the database table. Default = N",
            argdefault=False,
        )
        self.add_namedargdef(  # SQLWriter can append to exisiting tables with `ifExists`
            "append=<Y/N>",
            "str",
            "Specify whether to write new symbols to new tables in an existing database. Adding to existing tables is not allowed. Default: Create a new database file.",
            argdefault=False,
        )
        self.add_namedargdef(
            "unstack=<Y/N>",
            "str",
            "Specify if the last index column will be used as a header row.",
            argdefault=False,
        )

    def check_bool_args(self, key):
        """
        Helper function to convert the argVal of a boolean type argument to Boolean True/False.

        Raise Exception if the input is not y/n.
        """
        if key in self.namedargs:
            value = self.namedargs_val(key)
            if value.lower() in ["y", "yes"]:
                return True
            elif value.lower() in ["n", "no"]:
                return False
            self.tool_error(f"Wrong flag, {key}: {value}")

        return False

    def execute(self):
        if self.dohelp():
            return

        self.process_args()

        if self.namedargs_val("o"):
            sqlite_file = self.namedargs_val("o")
        elif not self.namedargs_val("o") and self.namedargs_val("gdxin"):
            sqlite_file = self.namedargs_val("gdxin").rsplit(".gdx", 1)[0] + ".db"
        else:
            self.tool_error(f"Option >o< not specified.")

        if not self.check_bool_args("append"):
            import os

            try:
                os.remove(sqlite_file)
            except FileNotFoundError:  # if not found, create the file
                pass
            except PermissionError as e:
                self.tool_error(f"Unable to delete {sqlite_file}.\n{e}")
            except Exception as e:
                self.tool_error(
                    f"An error occurred while deleting file >{sqlite_file}<:\n{e}"
                )

        skip_text = not self.check_bool_args("expltext")
        unstack = self.check_bool_args("unstack")

        from gams.connect import ConnectDatabase
        from gams import transfer as gt

        id_list = None  # reads all if ids is not set
        if "ids" in self.namedargs:
            id_list = self.namedargs_val("ids").split(",")

        cdb = ConnectDatabase(self._tools._system_directory, ecdb=self._tools._ecdb)
        m = cdb.container
        self.read_id_inputs(m, inputs=id_list)

        scalars = False
        scalar_parameter, scalar_variable, scalar_equation, symbols = [], [], [], []
        cc = m.data.copy()  # the following loop adds new symbols
        for sym_name, data in cc.items():
            if data.dimension == 0:
                scalars = True
                if isinstance(data, gt.Parameter):  # scalar parameter
                    scalar_parameter.append(sym_name)
                elif isinstance(data, gt.Variable):  # scalar variable
                    scalar_variable.append(sym_name)
                elif isinstance(data, gt.Equation):  # scalar equation
                    scalar_equation.append(sym_name)
            elif isinstance(data, gt.Variable) or isinstance(data, gt.Equation):
                dom = ",".join(f"d{i}" for i in range(data.dimension))
                cdb.execute(
                    {
                        "Projection": {
                            "name": f"{sym_name}.all({dom})",
                            "newName": f"{sym_name}_all({dom})",
                        }
                    }
                )
                symbols.append(
                    {
                        "name": f"{sym_name}_all",
                        "tableName": f"[{sym_name}]",
                        "unstack": True,
                    }
                )
            elif isinstance(data, gt.Alias):
                pass
            else:
                symbols.append({"name": sym_name, "tableName": f"[{sym_name}]"})

        if scalars:
            if scalar_parameter:
                cdb.execute(
                    {"Projection": {"name": scalar_parameter, "newName": "scalars"}}
                )
                m["scalars"].records = m["scalars"].records.rename(
                    columns={"uni_0": "name"}
                )
                symbols.append({"name": "scalars", "tableName": "scalars"})
            if scalar_variable:
                # combine all scalar variables into one
                cdb.execute(
                    {
                        "Projection": {
                            "name": scalar_variable,
                            "newName": "scalarvariables_dummy",
                        }
                    }
                )
                # convert the combined variable to parameter with variable attributes
                cdb.execute(
                    {
                        "Projection": {
                            "name": f"scalarvariables_dummy.all(i)",
                            "newName": f"scalarvariables(i)",
                        }
                    }
                )
                m["scalarvariables"].records = m["scalarvariables"].records.rename(
                    columns={"uni_0": "name"}
                )
                symbols.append(
                    {
                        "name": "scalarvariables",
                        "tableName": "scalarvariables",
                        "unstack": True,
                    }
                )
            if scalar_equation:
                # combine all scalar equations into one
                cdb.execute(
                    {
                        "Projection": {
                            "name": scalar_equation,
                            "newName": "scalarequations_dummy",
                        }
                    }
                )
                # convert the combined equation to parameter with equation attributes
                cdb.execute(
                    {
                        "Projection": {
                            "name": f"scalarequations_dummy.all(i)",
                            "newName": f"scalarequations(i)",
                        }
                    }
                )

                m["scalarequations"].records = m["scalarequations"].records.rename(
                    columns={"uni_0": "name"}
                )
                symbols.append(
                    {
                        "name": "scalarequations",
                        "tableName": "scalarequations",
                        "unstack": True,
                    }
                )

        sqlite_params = {
            "connection": {"database": sqlite_file},
            "trace": self.namedargs_val("trace"),
            "skipText": skip_text,
            "unstack": unstack,
            "symbols": symbols,
        }
        cdb.execute({"SQLWriter": sqlite_params})
