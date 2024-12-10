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

from gams.connect.agents.connectagent import ConnectAgent
import gams.transfer as gt
import numpy as np
import pandas as pd


class SQLReader(ConnectAgent):

    def __init__(self, cdb, inst):
        super().__init__(cdb, inst)
        inst_raw = inst
        inst = self._normalize_instructions(inst)
        self._parse_options(inst)
        self._inst = inst
        if self._trace > 0:
            self._log_instructions(inst, inst_raw)
        if self._trace > 3:
            pd.set_option("display.max_rows", None, "display.max_columns", None)

    def _parse_options(self, inst):
        self._connection = inst["connection"]
        self._connection_args = self._dict_get(inst, "connectionArguments", {})
        self._cnctn_type = inst["connectionType"]
        self._sym_type = inst["type"]
        self._symbols = inst["symbols"]
        self._dtype_map = inst["dTypeMap"]
        self._value_sub = inst["valueSubstitutions"]
        self._index_sub = inst["indexSubstitutions"]
        self._read_sql_args = inst["readSQLArguments"]
        self._trace = inst["trace"]

    def open(self):
        if self._cnctn_type == "sqlalchemy":
            import sqlalchemy

            con_str = sqlalchemy.engine.URL.create(**self._connection)
            self._engine = sqlalchemy.create_engine(con_str, **self._connection_args)
            self._conn = self._engine.connect()

        else:
            if self._cnctn_type in ["pyodbc", "access"]:
                import pyodbc as sql
            elif self._cnctn_type == "postgres":
                import psycopg2 as sql
            elif self._cnctn_type == "mysql":
                import pymysql as sql
            elif self._cnctn_type == "sqlserver":
                import pymssql as sql
            else:  # sqlite3 by default
                import sqlite3 as sql
            self._engine = sql.connect(**self._connection, **self._connection_args)
            self._conn = self._engine.cursor()

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")
        try:
            symbols_raw = self._symbols.copy()
            for s in self._symbols:
                self._update_sym_inst(s, self._inst)
            for sym, sym_raw in zip(self._symbols, symbols_raw):
                if sym["valueColumns"] == "infer":
                    if sym["type"] == "par":
                        sym["valueColumns"] = "lastCol"  # the last column will be a value column per default
                    elif sym["type"] == "set":
                        sym["valueColumns"] = "none"  # all columns will be index columns per default

                sym_name = sym["name"]
                sym_type = sym["type"]
                dtype_map = sym["dTypeMap"]
                value_col = sym["valueColumns"]
                index_sub = sym["indexSubstitutions"]
                value_sub = sym["valueSubstitutions"]
                read_sql_args = self._dict_get(sym, "readSQLArguments", {})

                if self._trace > 0:
                    self._log_instructions(
                        sym, sym_raw, description=f"Read symbol >{sym['name']}<:"
                    )

                self._check_symbol_exists(sym_name)

                if self._cnctn_type == "sqlalchemy":
                    df = pd.read_sql(sql=sym["query"], con=self._conn, **read_sql_args)
                else:
                    if (
                        len(read_sql_args) > 0
                    ):  # cannot pass an empty dictionary for pyODBC
                        self._conn.execute(sym["query"], read_sql_args)
                    else:
                        self._conn.execute(sym["query"])
                    df = pd.DataFrame.from_records(
                        self._conn.fetchall(),
                        columns=[col[0] for col in self._conn.description],
                    )

                if self._trace > 2:
                    self._cdb.print_log(f"DataFrame({sym_name}) after reading:\n{df}\n")

                cols = list(df.columns)

                if dtype_map:
                    df = df.astype(
                        {c: dtype_map[c] for c in cols if c in dtype_map.keys()}
                    )

                index_sub_flag = False
                stack = False
                if isinstance(value_col, str):
                    if value_col == "lastCol":
                        dim = len(cols) - 1
                        if dim > 0:
                            df.set_index(cols[:-1], inplace=True)
                        elif sym_type == "set":
                            self._connect_error(
                                "Dimension must be greater than 0 for a set."
                            )
                    elif value_col == "none":
                        if sym_type == "set":
                            df.set_index(cols, inplace=True)
                            index_sub_flag = True
                            dim = len(cols)
                        elif sym_type == "par":
                            self._connect_error(
                                "A parameter requires at least one value column."
                            )
                    else:
                        self._connect_error(
                            f"Invalid string >{value_col}< for valueColumns was passed."
                        )
                elif isinstance(value_col, list):
                    if len(value_col) == 0:
                        if sym_type == "set":
                            df.set_index(cols, inplace=True)
                            index_sub_flag = True
                            dim = len(cols)
                        else:
                            self._connect_error(
                                "A Parameter requires at least one value column."
                            )
                    else:
                        if all(x in cols for x in value_col):
                            index_col = [c for c in cols if c not in value_col]
                            if index_col != []:
                                df.set_index(index_col, inplace=True)
                            dim = len(index_col)
                            if (
                                len(value_col) > 1
                            ):  # automatically stack column names to index for more than one value/text column
                                stack = True
                                dim += 1
                        else:
                            not_in_df = list(set(value_col) - set(cols))
                            self._connect_error(
                                f"The following column(s) do not exist in the DataFrame({sym_name}): {not_in_df}"
                            )

                if self._trace > 2:
                    self._cdb.print_log(
                        f"DataFrame({sym_name}) after .set_index():\n{df}"
                    )

                domain = []
                if dim > 0:
                    if stack:
                        columns = df.columns
                        # stack from column axis to index axis
                        # pandas-version-check
                        if self._pandas_version_before(
                            pd.__version__, "2.2"
                        ):  # pandas < 2.2.0
                            df = df.stack(dropna=False)
                        else:  # pandas >= 2.2.0
                            df = df.stack(future_stack=True)
                        if dim == 1:
                            df = df.droplevel(
                                level=0
                            )  # drop pandas default index level
                        if self._trace > 1:
                            self._cdb.print_log(
                                "Automatically stack column names to index for more than one value/text column."
                            )
                        if self._trace > 2:
                            self._cdb.print_log(
                                f"DataFrame({sym_name}) after stack:\n{df}"
                            )

                    # write relaxed domain information
                    domain = [str(d) if d is not None else "*" for d in df.index.names]

                    df = df.reset_index()  # reset indices
                    if self._trace > 2:
                        self._cdb.print_log(
                            f"DataFrame({sym_name}) after .reset_index():\n{df}"
                        )
                    if index_sub:  # index substitution
                        if (
                            index_sub_flag
                        ):  # case where all columns in the dataFrame are set to indices
                            df = df.replace(index_sub)
                        else:  # inplace=True is not working since df.iloc[:,:-1] makes a copy
                            df.iloc[:, :-1] = df.iloc[:, :-1].replace(index_sub)
                        if self._trace > 2:
                            self._cdb.print_log(
                                f"DataFrame({sym_name}) after index substitution:\n{df}"
                            )
                        if stack:  # categories substitution
                            columns = pd.Index(pd.Series(columns).replace(index_sub))

                df = df.fillna(value=np.nan)
                if value_sub:  # value substitution
                    df.isetitem(-1, df.iloc[:, -1].replace(value_sub))
                    if self._trace > 2:
                        self._cdb.print_log(
                            f"DataFrame({sym_name}) after value substitution:\n{df}"
                        )

                if sym_type == "par":
                    sym = gt.Parameter(self._cdb.container, sym_name, domain=domain)
                    df = df.dropna()
                else:
                    sym = gt.Set(self._cdb.container, sym_name, domain=domain)
                    df = df.dropna()
                    if len(value_col) > 0 or value_col != "none":
                        df[df.columns[-1]] = df[df.columns[-1]].astype(str)

                df.columns = range(df.columns.size)  # reset column names

                if self._trace > 2:
                    self._cdb.print_log(
                        f"Final DataFrame({sym_name}) that will be processed by GAMSTransfer:\n{df}"
                    )

                sym.setRecords(df)

                if stack:
                    sym.records.isetitem(
                        dim - 1,
                        sym.records.iloc[:, dim - 1].astype(
                            pd.CategoricalDtype(
                                categories=columns.unique(), ordered=True
                            )
                        ),
                    )

        finally:
            if self._cnctn_type == "sqlalchemy":
                self._engine.dispose()
            else:
                self._conn.close()

        if self._trace > 2:
            for name, sym in self._cdb.container.data.items():
                self._cdb.print_log(
                    f"Connect Container symbol={name}:\n {sym.records}\n"
                )
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
