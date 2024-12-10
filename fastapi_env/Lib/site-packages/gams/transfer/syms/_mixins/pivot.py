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

from gams.transfer._internals import SpecialValues
import pandas as pd
from typing import Optional, Union


class PivotBase:
    def pivot(self, *args):
        index, columns = args

        #
        # ARG: self
        if self.dimension < 2:
            raise Exception(
                "Pivoting operations only possible on symbols with dimension > 1, "
                f"symbol dimension is {self.dimension}"
            )

        #
        # ARG: index
        if not isinstance(index, (str, list, type(None))):
            raise TypeError("Argument 'index' must be type str, list or NoneType")

        # set defaults
        if index is None:
            index = self.records.columns[: self.dimension - 1].tolist()

        if isinstance(index, str):
            index = [index]

        #
        # ARG: columns
        if not isinstance(columns, (str, list, type(None))):
            raise TypeError("Argument 'columns' must be type str, list, or NoneType")

        # set defaults
        if columns is None:
            columns = self.records.columns[self.dimension - 1 : self.dimension].tolist()

        if isinstance(columns, str):
            columns = [columns]

        #
        # ARG: index & columns
        if set(index + columns) != set(self.domain_labels):
            raise Exception(
                "Must specify all domain_labels to pivot in either 'index' or 'columns' "
                f"arguments, user did not specify: {set(self.domain_labels) - set(index+columns)}"
            )

        return index, columns


class PivotSetMixin(PivotBase):
    def pivot(
        self,
        index: Optional[Union[str, list]] = None,
        columns: Optional[Union[str, list]] = None,
        fill_value: Optional[Union[int, float, str]] = None,
    ) -> pd.DataFrame:
        """
        Convenience function to pivot records into a new shape (only symbols with >1D can be pivoted)

        Parameters
        ----------
        index : str | list, optional
            If index is None then it is set to dimensions [0..dimension-1], by default None
        columns : str | list, optional
            If columns is None then it is set to the last dimension, by default None
        fill_value : int | float | str, optional
            Missing values in the pivot will take the value provided by fill_value, by default None

        Returns
        -------
        DataFrame
            Pivoted records dataframe
        """
        # check & set
        index, columns = super().pivot(index, columns)
        value = "value"

        #
        # ARG: fill_value
        # set defaults
        if fill_value is None:
            fill_value = False

        # processing for Sets
        df = self.records.copy()
        df.drop(columns=["element_text"], inplace=True)
        df.insert(self.dimension, value, True)

        # do the pivot
        df = df.pivot(index=index, columns=columns, values=value)

        # fill missing values
        df.fillna(fill_value, inplace=True)

        # cast column types
        if isinstance(fill_value, bool):
            df = df.astype(bool)
        else:
            df = df.infer_objects()

        df.index.names = [None] * len(index)
        df.columns.names = [None] * len(columns)

        return df


class PivotParameterMixin(PivotBase):
    def pivot(
        self,
        index: Optional[Union[str, list]] = None,
        columns: Optional[Union[str, list]] = None,
        fill_value: Optional[Union[int, float, str]] = None,
    ) -> pd.DataFrame:
        """
        Convenience function to pivot records into a new shape (only symbols with >1D can be pivoted)

        Parameters
        ----------
        index : str | list, optional
            If index is None then it is set to dimensions [0..dimension-1], by default None
        columns : str | list, optional
            If columns is None then it is set to the last dimension, by default None
        fill_value : int | float | str, optional
            Missing values in the pivot will take the value provided by fill_value, by default None

        Returns
        -------
        DataFrame
            Pivoted records dataframe
        """
        # check & set
        index, columns = super().pivot(index, columns)
        value = "value"

        #
        # ARG: fill_value
        # set defaults
        if fill_value is None:
            fill_value = 0.0

        # do the pivot
        df = self.records[self.domain_labels + [value]]

        if any(i != i for i in df[value]):
            has_nans = True
        else:
            has_nans = False

        # do the pivot
        df = df.pivot(index=index, columns=columns, values=value)
        stored_columns = df.columns

        # fill missing values
        df.fillna(fill_value, inplace=True)

        # need to restore proper special values
        if has_nans:
            specnans = self.findSpecialValues(
                [SpecialValues.UNDEF, SpecialValues.NA], column=value
            )

            idx = list(zip(*[specnans[i] for i in index]))
            col = list(zip(*[specnans[i] for i in columns]))
            for n, (i, c) in zip(specnans.index, zip(idx, col)):
                df.loc[i, c] = specnans.loc[n, value]

            df.columns = stored_columns

        # cast column types
        if isinstance(fill_value, float):
            df = df.astype(float)
        else:
            df = df.infer_objects()

        df.index.names = [None] * len(index)
        df.columns.names = [None] * len(columns)

        return df


class PivotVariableMixin(PivotBase):
    def pivot(
        self,
        index: Optional[Union[str, list]] = None,
        columns: Optional[Union[str, list]] = None,
        value: Optional[str] = None,
        fill_value: Optional[Union[int, float, str]] = None,
    ) -> pd.DataFrame:
        """
        Convenience function to pivot records into a new shape (only symbols with >1D can be pivoted)

        Parameters
        ----------
        index : str | list, optional
            If index is None then it is set to dimensions [0..dimension-1], by default None
        columns : str | list, optional
            If columns is None then it is set to the last dimension, by default None
        value : str, optional
             If value is None then the level values will be pivoted, by default None
        fill_value : int | float | str, optional
            Missing values in the pivot will take the value provided by fill_value, by default None

        Returns
        -------
        DataFrame
            Pivoted records dataframe
        """
        # check & set
        index, columns = super().pivot(index, columns)

        #
        # ARG: value
        # set defaults
        if not isinstance(value, (str, type(None))):
            raise TypeError("Argument 'value' must be type str or NoneType")

        if value is None:
            value = "level"

        if value not in self._attributes:
            raise TypeError(
                f"Argument 'value' must be one of the following symbol attributes: {self._attributes}"
            )

        #
        # ARG: fill_value
        # set defaults
        if fill_value is None:
            fill_value = 0.0

        # do the pivot
        df = self.records[self.domain_labels + [value]]

        if any(i != i for i in df[value]):
            has_nans = True
        else:
            has_nans = False

        # do the pivot
        df = df.pivot(index=index, columns=columns, values=value)
        stored_columns = df.columns

        # fill missing values
        df.fillna(fill_value, inplace=True)

        # need to restore proper special values
        if has_nans:
            specnans = self.findSpecialValues(
                [SpecialValues.UNDEF, SpecialValues.NA], column=value
            )

            idx = list(zip(*[specnans[i] for i in index]))
            col = list(zip(*[specnans[i] for i in columns]))
            for n, (i, c) in zip(specnans.index, zip(idx, col)):
                df.loc[i, c] = specnans.loc[n, value]

            df.columns = stored_columns

        # cast column types
        if isinstance(fill_value, float):
            df = df.astype(float)
        else:
            df = df.infer_objects()

        df.index.names = [None] * len(index)
        df.columns.names = [None] * len(columns)

        return df


class PivotEquationMixin(PivotVariableMixin): ...
