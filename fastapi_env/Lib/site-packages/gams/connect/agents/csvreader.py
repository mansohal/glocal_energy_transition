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
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import copy
import os
from typing import Any, List, Optional, Union
import pandas as pd
from gams import transfer as gt
from gams.connect.agents.connectagent import ConnectAgent


class CSVReader(ConnectAgent):
    def __init__(self, cdb, inst):
        super().__init__(cdb, inst)
        inst_raw = inst
        inst = self._normalize_instructions(inst)
        self._parse_options(inst)
        if self._trace > 0:
            self._log_instructions(inst, inst_raw)
        if self._trace > 3:
            pd.set_option("display.max_rows", None, "display.max_columns", None)

        self._check_symbol_exists(self._name)
        self._check_invalid_input()
        self._read_csv_args.update(self._read_csv_arguments)

        self._index_cols = self._convert_to_valid_pd_cols(self._index_cols)
        self._value_cols = self._convert_to_valid_pd_cols(self._value_cols)
        self._check_cols()

        if self._stack == "infer":
            if len(self._value_cols) > 1 or self._multiheader:
                self._stack = True
            else:
                self._stack = False

    def _parse_options(self, inst):
        inst["file"] = os.path.abspath(inst["file"])
        self._file = inst["file"]
        self._name = inst["name"]
        self._names = inst["names"]
        self._sym_type = inst["type"]
        self._index_cols = inst["indexColumns"]
        self._index_sub = self._dict_get(inst, "indexSubstitutions", {})
        self._value_cols = inst["valueColumns"]
        self._value_sub = self._dict_get(inst, "valueSubstitutions", {})
        self._trace = inst["trace"]
        self._header = inst["header"]
        self._skip_rows = inst["skipRows"]
        self._read_csv_arguments = self._dict_get(inst, "readCSVArguments", {})
        self._field_sep = inst["fieldSeparator"]
        self._decimal_sep = inst["decimalSeparator"]
        self._thousands_sep = inst["thousandsSeparator"]
        self._quoting = inst["quoting"]
        self._auto_col = inst["autoColumn"]
        self._auto_row = inst["autoRow"]
        self._stack = inst["stack"]
        self._multiheader = True if isinstance(self._header, list) else False
        self._header = self._parse_header()

        if isinstance(self._skip_rows, list):
            # pandas skiprows is 0-indexed
            self._skip_rows = [i - 1 for i in self._skip_rows]

        self._read_csv_args = {
            "header": self._header,
            "names": self._names,
            "skiprows": self._skip_rows,
            "sep": self._field_sep,
            "decimal": self._decimal_sep,
            "thousands": self._thousands_sep,
            "quoting": self._quoting,
        }

    def _check_invalid_input(self):
        if self._multiheader:
            if self._sym_type == "set":
                self._connect_error(
                    "Reading sets with multi-row headers is not supported."
                )

            if self._stack is False:
                self._connect_error(
                    f"Multi-row header needs to be stacked to index but stack is set to >{self._stack}<."
                )

            if self._value_cols:
                self._connect_error(
                    "Cannot specify valueColumns if the data has a multi-row"
                    " header. All columns that are not indexColumns will be"
                    " read as valueColumns."
                )

            if isinstance(self._index_cols, list) and all(
                isinstance(col, str) for col in self._index_cols
            ):
                self._connect_error(
                    "The CSVReader with multi-row header does not support to"
                    " specify indexColumns as column names. Please provide"
                    " column positions instead."
                )
            # consequently, multi-row header also does not support order of valueColumns
            # and the same column in both indexColumns and valueColumns
        elif self._sym_type == "par" and (
            self._value_cols is None or self._value_cols == []
        ):
            self._connect_error(
                "Symbol type parameter requires at least one value column."
            )

        if self._multiheader and self._auto_col:
            self._connect_error("Cannot use autoColumn with multi-row header.")

        if self._multiheader and self._auto_row:
            self._connect_error("Cannot use autoRow with multi-row header.")

        if (
            self._stack is True
            and self._header is None
            and self._names is None
            and self._auto_col is None
        ):
            self._connect_error("Cannot stack without a header, names or autoColumn.")

    def _parse_header(self) -> Optional[Union[int, list]]:
        """
        Returns the header value that will be provided to pandas
        read_csv method according to the user input

        Returns
        -------
        int | list | None
            Header value
        """

        # Infer: header True (0) if no names are provided otherwise False (None)
        if self._header == "infer":
            if self._names is None:
                return 0
            return None

        # For non-multirow header, user inputs are booleans (True or False).
        if self._header is False:
            return None

        if self._header is True:
            return 0

        if isinstance(self._header, list):
            # pandas header is 0-indexed
            return [i - 1 for i in self._header]

    def _get_last_column(self) -> str:
        """Returns the position of the last column

        Returns
        -------
        str
            Position of the last column
        """
        read_header_args = copy.deepcopy(self._read_csv_args)
        if self._header is not None or self._names is not None:
            read_header_args.update({"nrows": 0})

            if self._trace > 1:
                self._cdb.print_log(
                    "Calculate symbolic constant lastCol by reading the"
                    " header row. Arguments for reading the header"
                    f" row:\n{read_header_args}"
                )

        else:
            read_header_args.update({"header": None, "nrows": 1})

            if self._trace > 1:
                self._cdb.print_log(
                    "Calculate symbolic constant lastCol by reading the"
                    " first line of data. Arguments for reading the first"
                    f" line of data:\n{read_header_args}"
                )

        header_row = pd.read_csv(self._file, **read_header_args)

        return str(len(header_row.columns))

    def _convert_to_valid_pd_cols(self, cols: Any) -> Union[List[int], List[str]]:
        """Converts user provided indexColumns or valueColumns
        to valid pandas columns

        Parameters
        ----------
        cols : Any
            Columns provided by the user

        Returns
        -------
        list
            Column positions or names
        """

        if isinstance(cols, str):
            if "lastcol" in cols.lower():
                last_col = self._get_last_column()
                cols = cols.lower().replace("lastcol", last_col)
            try:
                positions = [
                    (
                        list(
                            range(
                                *[
                                    int(value) + index
                                    for index, value in enumerate(position.split(":"))
                                ]
                            )
                        )
                        if ":" in position
                        else [int(position)]
                    )
                    for position in cols.split(",")
                ]

                # convert to 0-indexed
                cols = [i - 1 for sublist in positions for i in sublist]
            except Exception:
                self._connect_error(
                    "Column assignation as string can only include"
                    " integers, comma (,), colon (:) and symbolic constant"
                    " lastCol."
                )
        elif isinstance(cols, list):
            if all(isinstance(i, int) for i in cols):
                cols = [i - 1 for i in cols]  # convert to 0-indexed
        elif isinstance(cols, int):
            cols = [cols - 1]
        else:
            cols = []

        return cols

    def _check_cols(self):
        if self._stack is False and len(self._value_cols) > 1:
            self._connect_error(
                f"For more than one value column the column names need to be stacked to index but stack is set to >{self._stack}<."
            )

        if not all(
            isinstance(i, str) for i in self._index_cols + self._value_cols
        ) and not all(isinstance(i, int) for i in self._index_cols + self._value_cols):
            self._connect_error(
                "Index and value columns must be either given as positions or"
                " names not both."
            )

        if len(self._index_cols) != len(set(self._index_cols)) or len(
            self._value_cols
        ) != len(set(self._value_cols)):
            self._connect_error("Duplicates in index and value columns not allowed.")

        if len(self._value_cols) > 1:
            if self._header is None and self._names is None and self._auto_col is None:
                self._connect_error(
                    "More than one value column requires a header, names"
                    " or autoColumn."
                )

    def _get_dtypes(
        self,
        index_col: Optional[Union[List[int], List[str]]],
        usecols: Union[List[int], List[str]],
    ) -> dict:
        """Returns the data types for index and text columns

        Parameters
        ----------
        index_col : List[int] | List[str] | None
            Index columns to be used for read_csv
        usecols : List[int] | List[str]
            All columns to be used

        Returns
        -------
        dict
            Updated data types for columns
        """
        col_dtype = {}

        if index_col is not None:
            col_dtype.update({i: str for i in index_col})

        if self._sym_type == "set" and len(self._value_cols) > 0:
            value_col = [sorted(usecols).index(i) for i in self._value_cols]
            col_dtype.update({i: str for i in value_col})

        return col_dtype

    def _substitute_index(self, df: pd.DataFrame) -> None:
        """Inplace index substitution

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to be manipulated
        """
        if self._sym_type == "set" and len(self._value_cols) == 0:
            df.replace(self._index_sub, inplace=True)
        else:
            df.iloc[:, :-1] = df.iloc[:, :-1].replace(self._index_sub)

        if self._trace > 2:
            self._cdb.print_log(f"DataFrame after index substitution:\n{df}")

    def _substitute_values(self, df: pd.DataFrame):
        """Inplace value substitution

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to be manipulated
        """
        # pandas-version-check
        if self._pandas_version_before(pd.__version__, "2.2"):  # pandas < 2.2.0
            df.isetitem(-1, df.iloc[:, -1].replace(self._value_sub))
        else:  # pandas >= 2.2.0
            with pd.option_context("future.no_silent_downcasting", True):
                df.isetitem(-1, df.iloc[:, -1].replace(self._value_sub).infer_objects())

        if self._trace > 2:
            self._cdb.print_log(f"DataFrame after value substitution:\n{df}")

    def _generate_row_labels(self, df: pd.DataFrame) -> None:
        """Generates row labels for autoRow option

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to be manipulated
        """
        if self._index_cols:
            index_frame = df.index.to_frame()
            index_frame.insert(
                0,
                "autoRow",
                [self._auto_row + str(i + 1) for i in range(len(df.index))],
                True,
            )

            df.index = pd.MultiIndex.from_frame(index_frame)
        else:
            df.rename(
                {i: self._auto_row + str(i + 1) for i in list(df.index)},
                axis="index",
                inplace=True,
            )

        if self._trace > 2:
            self._cdb.print_log(f"DataFrame after inserting autoRow:\n{df}")

    def _generate_column_labels(self, df: pd.DataFrame) -> None:
        """Generates columns labels for autoColumn option

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to be manipulated
        """
        if (self._header is not None or self._names is not None) and self._trace > 1:
            self._cdb.print_log("autoColumn overrides existing column names.")

        df.rename(
            {c: self._auto_col + str(i + 1) for i, c in enumerate(list(df.columns))},
            axis="columns",
            inplace=True,
        )

        if self._trace > 2:
            self._cdb.print_log(f"DataFrame after inserting autoColumn:\n{df}")

    def _set_categoricals(
        self, symbol: Union["gt.Set", "gt.Parameter"], dim: int, columns: list
    ) -> None:
        """Sets the categoricals for the Gams Transfer symbol records

        Parameters
        ----------
        symbol : gt.Set | gt.Parameter
            Symbol for setting the categoricals
        dim : int
            Dimension to set the categories on
        columns : list
            Column names for categories
        """
        symbol.records.isetitem(
            dim,
            symbol.records.iloc[:, dim].astype(
                pd.CategoricalDtype(
                    categories=columns.map(str).map(str.rstrip).unique(),
                    ordered=True,
                )
            ),
        )

    def _stack_multiheader(self, df: pd.DataFrame) -> pd.DataFrame:
        """Stacks column names to index for a multi-row header

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to be stacked

        Returns
        -------
        pd.DataFrame
            Stacked DataFrame
        """
        # Make index and column names unique
        df.columns.names = [f"column_{i}" for i in range(len(df.columns.names))]

        df.index.names = [f"row_{i}" for i in range(len(df.index.names))]

        # Stack columns to index
        # pandas-version-check
        if self._pandas_version_before(pd.__version__, "2.2"):  # pandas < 2.2.0
            df = df.stack(level=df.columns.names, dropna=False)
        else:  # pandas >= 2.2.0
            df = df.stack(level=df.columns.names, future_stack=True)

        return df

    def _sort_value_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sorts value columns according to the order specified

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to be sorted

        Returns
        -------
        pd.DataFrame
            DataFrame with sorted value columns
        """
        value_cols = [c for c in self._value_cols if c not in self._index_cols]

        if len(value_cols) > 1:
            if all(isinstance(i, int) for i in value_cols):
                value_cols_order = [
                    df.columns[sorted(value_cols).index(i)] for i in value_cols
                ]
            else:
                value_cols_order = value_cols

            df = df[value_cols_order]

            if self._trace > 2:
                self._cdb.print_log(f"DataFrame after reordering value columns:\n{df}")

        return df

    def _copy_from_index_to_value(
        self, df: pd.DataFrame, index_col, usecols
    ) -> pd.DataFrame:
        """If columns appear both in index and value columns, pd.read_csv only
        adds the column to index and we copy it to the value column

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to be extended
        index_col : list | None
            argument passed to pd.read_csv method
        usecols : list
            argument passed to pd.read_csv method

        Returns
        -------
        pd.DataFrame
            Extended DataFrame
        """
        if any(c in self._value_cols for c in self._index_cols):
            value_cols = self._value_cols
            if all(isinstance(i, int) for i in value_cols):
                value_cols = [sorted(usecols).index(i) for i in value_cols]
            for i, c in enumerate(value_cols):
                if c in index_col:
                    index_name = df.index.names[index_col.index(c)]
                    df.insert(i, index_name, df.index.get_level_values(index_name))
            if self._trace > 2:
                self._cdb.print_log(
                    f"DataFrame after duplicating index to value column:\n{df}"
                )

        return df

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")

        usecols = self._index_cols + self._value_cols

        # no duplicates in usecols, since pd.read_csv ignores duplicates in usecols and the indices in index_col do not match anymore
        usecols = list(dict.fromkeys(usecols))

        if self._index_cols:
            if all(isinstance(i, int) for i in usecols) and not self._multiheader:
                index_col = [sorted(usecols).index(i) for i in self._index_cols]
            else:
                index_col = self._index_cols
        else:
            index_col = None

        # default dtype of index and text columns should be string
        if "dtype" not in self._read_csv_args.keys():
            dtypes = self._get_dtypes(index_col, usecols)
            self._read_csv_args.update({"dtype": dtypes})

        self._read_csv_args.update({"index_col": index_col})

        # Multi-row header does not support usecols, therefore, we only
        # support reading all columns and not a subset
        if not self._multiheader:
            self._read_csv_args.update({"usecols": usecols})

        if self._trace > 1:
            self._cdb.print_log(
                f"Arguments for reading the CSV file:\n{self._read_csv_args}"
            )

        df = pd.read_csv(self._file, **self._read_csv_args)

        if self._trace > 2:
            self._cdb.print_log(
                f"Raw DataFrame directly after reading the CSV file:\n{df}"
            )

        df = self._sort_value_columns(df)
        df = self._copy_from_index_to_value(df, index_col, usecols)

        dim = len(self._index_cols)
        # write relaxed domain information
        if dim == 0:
            domain = []
        else:
            domain = [str(d) if d is not None else "*" for d in df.index.names]

        if self._auto_row is not None and not df.index.empty:
            self._generate_row_labels(df)

            dim += 1
            domain.insert(0, "*")

        if self._auto_col is not None and not df.columns.empty:
            self._generate_column_labels(df)

            if self._stack:
                dim += 1
                domain.append("*")

        elif self._stack:
            if self._multiheader:
                dim += len(self._header)
                domain.extend(
                    [str(d) if d is not None else "*" for d in df.columns.names]
                )
            else:
                dim += 1
                domain.append("*")

        if dim > 0:
            if self._stack:
                columns = df.columns

                # stack from column axis to index axis
                if self._multiheader:
                    df = self._stack_multiheader(df)
                else:
                    # pandas-version-check
                    if self._pandas_version_before(
                        pd.__version__, "2.2"
                    ):  # pandas < 2.2.0
                        df = df.stack(dropna=False)
                    else:  # pandas >= 2.2.0
                        df = df.stack(future_stack=True)

                if dim == 1 or (self._multiheader and dim == columns.nlevels):
                    # drop pandas default index level
                    df = df.droplevel(level=0)

                if self._trace > 1:
                    self._cdb.print_log(
                        "Automatically stack column names to index for more"
                        " than one value column."
                    )
                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame after stack:\n{df}")

            df = df.reset_index(allow_duplicates=True)

            if self._trace > 2:
                self._cdb.print_log(f"DataFrame after .reset_index():\n{df}")

            # index substitution
            if self._index_sub:
                self._substitute_index(df)

                # Substitute in categoricals
                if self._stack:
                    if self._multiheader:
                        mod_columns = []
                        for i in range(columns.nlevels):
                            c = columns.get_level_values(level=i)
                            mod_columns.append(pd.Series(c).replace(self._index_sub))
                        columns = pd.MultiIndex.from_arrays(mod_columns)
                    else:
                        columns = pd.Index(pd.Series(columns).replace(self._index_sub))

        elif self._sym_type == "set":
            self._connect_error("Symbol type set requires at least one index column.")

        if self._value_sub and (self._sym_type == "par" or self._value_cols):
            self._substitute_values(df)
        df.dropna(inplace=True)

        if self._sym_type == "par":
            sym = gt.Parameter(self._cdb.container, self._name, domain=domain)
        else:
            sym = gt.Set(self._cdb.container, self._name, domain=domain)

        # reset the index to the default integer index
        df = df.reset_index(drop=True)

        if self._trace > 2:
            self._cdb.print_log(
                "Final DataFrame that will be processed by" f" GAMSTransfer:\n{df}"
            )

        sym.setRecords(df)

        if dim > 0 and self._stack:
            if self._multiheader:
                # Reset domain labels
                sym.domain_labels = domain
                # Set categoricals to preserve uel order
                for i in range(columns.nlevels):
                    c = columns.get_level_values(level=i)
                    c_dim = dim - columns.nlevels + i
                    self._set_categoricals(sym, c_dim, c)
            else:
                # Set categoricals to preserve uel order
                self._set_categoricals(sym, dim - 1, columns)

        if self._trace > 2:
            self._cdb.print_log(
                f"Connect Container symbol={self._name}:\n {sym.records}\n"
            )

        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
