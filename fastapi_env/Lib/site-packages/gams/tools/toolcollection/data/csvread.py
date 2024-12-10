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
import os


class Csvread(ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = "csvread: This tool writes data from a csv file to a gdx file."
        self.add_posargdef("filename", "fnExist", "Specify a CSV file path.")
        self.add_namedargdef(
            "id=<string>",
            "str",
            "Specify a symbol name for the Connect database.",
        )
        self.add_namedargdef(
            "useHeader=<boolean>",
            "str",
            "Specify the header used as the column names.",
            argdefault="N",
        )
        self.add_namedargdef(
            "autoCol=<string>",
            "str",
            "Generate automatic column names.",
            argdefault=None,
        )
        self.add_namedargdef(
            "autoRow=<string>", "str", "Generate automatic row labels.", argdefault=None
        )
        self.add_namedargdef(
            "index=<string>",
            "str",
            "Specify columns to use as the row labels.",
            argdefault=None,
        )
        self.add_namedargdef(
            "values=<string>",
            "str",
            "Specify columns to get the values from.",
            argdefault=None,
        )
        self.add_namedargdef(
            "text=<string>",
            "str",
            "Specify columns to get the set element text from.",
            argdefault=None,
        )
        self.add_namedargdef(
            "quoting=<int>", "int", "Control field quoting behavior.", argdefault=0
        )
        self.add_namedargdef(
            "fieldSep=<string>", "str", "Specify a field separator.", argdefault="comma"
        )
        self.add_namedargdef(
            "decimalSep=<string>",
            "str",
            "Specify a decimal separator. ",
            argdefault="period",
        )
        self.add_namedargdef(
            "thousandsSep=<string>",
            "str",
            "Specify a thousands separator.",
            argdefault=None,
        )
        self.add_namedargdef(
            "gdxOut=<filename>",
            "fnWriteable",
            "Specify the name for the GDX file.",
            argdefault=None,
            shell_req=True,
        )
        self.add_namedargdef(
            "checkDate=<boolean>",
            "str",
            "Write GDX file only if the CSV file is more recent than the GDX file.",
            argdefault="N",
        )
        self.add_namedargdef(
            "valueDim=<boolean>",
            "str",
            "Stacks the column names to index.",
            argdefault="N",
        )  # this is the stack option in CSVReader
        self.add_namedargdef(
            "argsFile=<filename>",
            "fnExist",
            "Specify the arguments file path.",
            argdefault=None,
        )
        self.add_namedargdef(
            "acceptBadUels=<boolean>",
            "str",
            "Indicate if bad UELs are accepted or result in an error return code.",
            argdefault="N",
        )
        self.add_namedargdef(
            "dimIds=<list>",
            "str",
            "Indicate which dimensions are written",
        )

        self._csvreader_params, self._other_params = {}, {}
        self._params_mapper = {
            "id": "name",
            "trace": "trace",
            "useheader": "header",
            "autocol": "autoColumn",
            "autorow": "autoRow",
            "index": "indexColumns",
            "values": "valueColumns",
            "text": "textColumns",  # textColumns has been removed. Instead use `valueColumns` and `type=set`. We update this later.
            "quoting": "quoting",
            "fieldsep": "fieldSeparator",
            "decimalsep": "decimalSeparator",
            "thousandssep": "thousandsSeparator",
            "valuedim": "stack",
        }

    @staticmethod
    def check_duplicate_in_named_args(tuple_list):
        seen_elements = set()
        duplicates = set()

        for tup in tuple_list:
            if tup[0] in seen_elements:
                duplicates.add(tup[0])
            else:
                seen_elements.add(tup[0])

        return ", ".join(duplicates)

    def read_params_file(self):
        """
        Helper function to read a parameter file. Lines starting with * are ignored.
        """
        csvreader_params = {}
        other_params = {}
        with open(self.namedargs_val("argsFile"), "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("*") or "=" not in line:
                    continue
                key, value = map(str.strip, line.split("=", 1))
                value = self.check_bool_args(key, value)
                if key.lower() in self._params_mapper:
                    csvreader_params[self._params_mapper[key.lower()]] = value
                else:
                    other_params[key.lower()] = value
        self._csvreader_params.update(csvreader_params)
        self._other_params.update(other_params)

    def check_date(self, in_file, out_file, trace):
        """
        Helper function to check if CSV is older than GDX, which in turn would not create a new GDX.

        Ignore the Exception if checkDate is set to True and gdx is not yet created.
        """
        try:
            if os.path.getmtime(in_file) < os.path.getmtime(out_file) and trace > 0:
                self._tools.print_log(
                    f"No new file written, >checkDate< is set to True."
                )
            exit(0)
        except (
            FileNotFoundError
        ):  # if checkDate is set to 'Y' and gdx file does not exist
            pass

    def check_bool_args(self, key, value):
        """
        Helper function to convert the argVal of a boolean type argument to Boolean True/False.
        Returns the specified value in case the option is not a boolean type argument.

        Raise Exception if the input is not y/n or Y/N.
        """
        if key.lower() in [
            "checkdate",
            "acceptbaduels",
            "valuedim",
            "useheader",
        ]:
            if value.lower() in ["y", "yes"]:
                return True
            elif value.lower() in ["n", "no"]:
                return False
            self.tool_error(f"Wrong flag, {key}: {value}", print_help=False)
        return value

    def generate_csv_params(self):
        """
        Helper function to add arguments in the CSVReader agent only if the options were specified.
        """
        csv_params_dict = {}
        other_params = {}

        if self.namedargs_val("argsFile") is not None:
            self.read_params_file()

        for ele in self.namedargs:
            val = self.check_bool_args(ele, self.namedargs_val(ele))
            if ele in self._params_mapper:
                csv_params_dict[self._params_mapper[ele]] = val
            else:
                other_params[ele] = val
        self._csvreader_params.update(csv_params_dict)
        self._other_params.update(other_params)

    def check_bad_uels(self, df):
        """
        Helper function to check if there are bad UELs present in any of the index columns.

        returns:
            bad_cols: List of columns containing bad UELs
        """
        columns = df.columns[:-1]
        bad_cols = []
        for col in columns:
            lengths = df[col].apply(len).tolist()
            if any(len >= 64 for len in lengths):
                bad_cols.append(col)
        return bad_cols

    @staticmethod
    def accept_bad_uels(df):
        """
        Helper function to utilize the `acceptBadUels` option as in CSV2GDX.

        Converts every bad UEL, i.e., element longer than 63 to a defined label.
        """
        cols = df.columns[:-1]
        for i, col in enumerate(cols):
            df[col] = df[col].apply(
                lambda x: (
                    f"Bad_Line_{df[df[col] == x].index[0]+1}_Dim_{i+1}"
                    if len(x) >= 64
                    else x
                )
            )

        return df

    def replace_dots_with_colons(self):
        if (
            "valueColumns" in self._csvreader_params
            and ".." in self._csvreader_params["valueColumns"]
        ):
            self._csvreader_params["valueColumns"] = self._csvreader_params[
                "valueColumns"
            ].replace("..", ":")

        if (
            "indexColumns" in self._csvreader_params
            and ".." in self._csvreader_params["indexColumns"]
        ):
            self._csvreader_params["indexColumns"] = self._csvreader_params[
                "indexColumns"
            ].replace("..", ":")

    def set_default_sep_values(self, flag):
        separators = {
            "fieldSeparator": {"comma": ",", "semicolon": ";", "tab": "\t"},
            "decimalSeparator": {"period": ".", "comma": ","},
        }
        default_sep = {"fieldSeparator": ",", "decimalSeparator": "."}

        if flag in self._csvreader_params:
            if separators[flag].get(self._csvreader_params[flag].lower()) is not None:
                self._csvreader_params[flag] = separators[flag].get(
                    self._csvreader_params[flag].lower()
                )
            else:
                self.tool_error(
                    f"Wrong {flag} input: {self._csvreader_params[flag]}",
                    print_help=False,
                )
        else:
            self._csvreader_params[flag] = default_sep[flag]

    @staticmethod
    def map_special_values():
        """
        This function preserves the old mapping of special values in CSV2GDX.
        """
        from gams.transfer import SpecialValues as sv
        from itertools import product

        mapper = {
            "": sv.NA,
            "yes": 1.0,
            "true": 1.0,
            "no": 0.0,
            "false": 0.0,
            "none": 0.0,
            "null": 0.0,
            "eps": sv.EPS,
            "n/a": sv.NA,
            "inf": sv.POSINF,
            "+inf": sv.POSINF,
            "-inf": sv.NEGINF,
        }
        exhaustive_mapper = {}
        for key, value in mapper.items():
            case_permutations = map(
                "".join, product(*((char.upper(), char.lower()) for char in key))
            )
            for perm in case_permutations:
                exhaustive_mapper[perm] = value
        return exhaustive_mapper

    def fetch_dimensions(self, df, m, dim_list):
        """
        Method to fetch the dimensions of the symbol and add new Set symbols in the container.
        """
        import pandas as pd

        if len(dim_list) > 0:
            if len(dim_list) > len(df.columns) - 1:
                self.tool_error(
                    f"Specified more dimensions >{len(dim_list)}< than available >{len(df.columns)-1}<",
                    print_help=False,
                )
            df = df.iloc[:, : len(dim_list)]
            df.columns = dim_list
        elif "gdxout" in self.namedargs:
            df = df[df.columns[:-1]]
            df.columns = [f"dim{i}" for i, _ in enumerate(df.columns, 1)]
        else:
            return list()

        category_lists = {}
        for col in dict.fromkeys(df.columns).keys():
            if isinstance(df[col], pd.DataFrame):
                category_lists[col] = pd.unique(df[col].values.ravel()).tolist()
            else:
                category_lists[col] = df[col].cat.categories.tolist()

        for name, records in category_lists.items():
            m.addSet(name=name, records=records)

        return list(category_lists.keys())

    def execute(self):
        if self.dohelp():
            return

        self.process_args()

        check_dupe_opts = self.check_duplicate_in_named_args(self.namedargs_list)
        if check_dupe_opts:
            self.tool_error(f"Duplicate option: {check_dupe_opts}", print_help=False)

        filename = self.posargs[0]

        self.generate_csv_params()

        try:
            sym_name = self._csvreader_params["name"]
        except KeyError:
            self.tool_error("parameter >id< not set.")

        trace = self._csvreader_params.get("trace", self.namedargs_val("trace"))
        sym_type = "par"

        if {"textColumns", "valueColumns"}.issubset(self._csvreader_params):
            self.tool_error(
                "Cannot set both text and values options at the same time.",
                print_help=False,
            )

        if (
            "textColumns" in self._csvreader_params
            or "indexColumns" in self._csvreader_params
        ) and ("valueColumns" not in self._csvreader_params):
            sym_type = "set"
            if "textColumns" in self._csvreader_params:
                self._csvreader_params["valueColumns"] = self._csvreader_params.pop(
                    "textColumns"
                )

        if (
            "valueColumns" not in self._csvreader_params
            and "stack" in self._csvreader_params
        ):  # CSV2GDX ignores valuedim if values are not present
            self._csvreader_params["stack"] = False

        if self._other_params.get("checkdate", None):
            self.check_date(
                in_file=filename, out_file=self.namedargs["gdxout"], trace=trace
            )

        self.replace_dots_with_colons()
        self.set_default_sep_values(flag="fieldSeparator")
        self.set_default_sep_values(flag="decimalSeparator")

        from gams.connect import ConnectDatabase

        cdb = ConnectDatabase(self._tools._system_directory, ecdb=self._tools._ecdb)
        m = cdb.container

        dim_list = []
        if self._other_params.get("dimids", None):
            dim_list = list(self._other_params["dimids"].split(","))

        csv_params = {
            "file": filename,
            "name": sym_name,
            "trace": trace,
            "header": self._csvreader_params.get("header", False),
            "type": sym_type,
            "valueSubstitutions": self.map_special_values(),
            "readCSVArguments": {"skipinitialspace": True, "keep_default_na": False},
        }

        self._csvreader_params.update(csv_params)
        try:
            cdb.execute({"CSVReader": self._csvreader_params})
        except Exception as e:
            self.tool_error(f"{e.__class__.__name__} : {e}", print_help=False)

        bad_uels = self.check_bad_uels(df=m[sym_name].records)
        if bad_uels:
            if self._other_params.get("acceptbaduels", None):
                self.accept_bad_uels(df=m[sym_name].records)
                self._tools.print_log(f"Bad Uels in col {bad_uels} were changed.")
            else:
                self.tool_error(
                    f"BadUels in col {bad_uels}, toggle option >acceptBadUels<."
                )

        sym_lists = [sym_name]
        df = m[sym_name].records

        sym_lists = [sym_name] + self.fetch_dimensions(df, m, dim_list)

        self.write_id_outputs(m, sym_lists)
