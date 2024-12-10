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

import numpy as np
import pandas as pd
from gams.transfer._internals import SpecialValues
import gams.transfer._abcs as abcs
from typing import Optional, Union, List


class PVEMixin:
    @property
    def shape(self) -> tuple:
        """
        Returns a tuple describing the array dimensions if records were converted with .toDense()

        Returns
        -------
        tuple
            A tuple describing the records dimensions
        """
        if self.domain_type == "regular":
            return tuple(
                [
                    (
                        0
                        if i.getUELs(0, ignore_unused=True) is None
                        else len(i.getUELs(0, ignore_unused=True))
                    )
                    for i in self.domain
                ]
            )
        else:
            return tuple(
                [
                    (
                        0
                        if self.getUELs(i, ignore_unused=True) is None
                        else len(self.getUELs(i, ignore_unused=True))
                    )
                    for i in range(self.dimension)
                ]
            )

    @property
    def is_scalar(self) -> bool:
        """
        Returns True if the len(self.domain) = 0

        Returns
        -------
        bool
            True if the len(self.domain) = 0
        """
        return self.dimension == 0

    def findEps(self, column: Optional[str] = None) -> pd.DataFrame:
        """
        Find positions of SpecialValues.EPS in value column

        Parameters
        ----------
        column : str, optional
            Column to find the special values in, by default None

        Returns
        -------
        pd.DataFrame
            Dataframe containing special values
        """
        return self.findSpecialValues(SpecialValues.EPS, column=column)

    def findNA(self, column: Optional[str] = None) -> pd.DataFrame:
        """
        Find positions of SpecialValues.NA in value column

        Parameters
        ----------
        column : str, optional
            Column to find the special values in, by default None

        Returns
        -------
        pd.DataFrame
            Dataframe containing special values
        """
        return self.findSpecialValues(SpecialValues.NA, column=column)

    def findUndef(self, column: Optional[str] = None) -> pd.DataFrame:
        """
        Find positions of SpecialValues.Undef in value column

        Parameters
        ----------
        column : str, optional
            Column to find the special values in, by default None

        Returns
        -------
        pd.DataFrame
            Dataframe containing special values
        """
        return self.findSpecialValues(SpecialValues.UNDEF, column=column)

    def findPosInf(self, column: Optional[str] = None) -> pd.DataFrame:
        """
        Find positions of SpecialValues.PosInf in value column

        Parameters
        ----------
        column : str, optional
            Column to find the special values in, by default None

        Returns
        -------
        pd.DataFrame
            Dataframe containing special values
        """
        return self.findSpecialValues(SpecialValues.POSINF, column=column)

    def findNegInf(self, column: Optional[str] = None) -> pd.DataFrame:
        """
        Find positions of SpecialValues.NegInf in value column

        Parameters
        ----------
        column : str, optional
            Column to find the special values in, by default None

        Returns
        -------
        pd.DataFrame
            Dataframe containing special values
        """
        return self.findSpecialValues(SpecialValues.NEGINF, column=column)

    def findSpecialValues(
        self, values: Union[float, List[float]], column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Find positions of specified values in records columns

        Parameters
        ----------
        values : float | List[float]
            Values to look for
        column : str, optional
            Column to find the special values in, by default None

        Returns
        -------
        pd.DataFrame
            Dataframe containing special values
        """
        # ARG: values
        if not isinstance(values, (float, list)):
            raise TypeError("Argument 'values' must be type float or list")

        if isinstance(values, float):
            values = [values]

        for i in values:
            if not (
                SpecialValues.isEps(i)
                or SpecialValues.isNA(i)
                or SpecialValues.isUndef(i)
                or SpecialValues.isPosInf(i)
                or SpecialValues.isNegInf(i)
            ):
                return ValueError(
                    "Argument 'values' is currently limited to one of the "
                    "five special value constants defined as: "
                    "EPS, NA, UNDEF, POSINF, or NEGINF"
                )

        # ARG: columns
        # set defaults
        if column is None:
            if isinstance(self, abcs.ABCParameter):
                column = "value"
            elif isinstance(self, (abcs.ABCVariable, abcs.ABCEquation)):
                column = "level"
            else:
                raise Exception(f"Unsupported object type: {type(self)}")

        # checks
        if not isinstance(column, str):
            raise TypeError(
                f"Argument 'column' must be type str. User passed {type(column)}."
            )

        if column not in self._attributes:
            raise TypeError(
                f"Argument 'column' must be a one of the following: {self._attributes}"
            )

        if self.records is not None:
            for n, i in enumerate(values):
                if n == 0:
                    if SpecialValues.isEps(i):
                        idx = SpecialValues.isEps(self.records[column])
                    elif SpecialValues.isNA(i):
                        idx = SpecialValues.isNA(self.records[column])
                    elif SpecialValues.isUndef(i):
                        idx = SpecialValues.isUndef(self.records[column])
                    elif SpecialValues.isPosInf(i):
                        idx = SpecialValues.isPosInf(self.records[column])
                    elif SpecialValues.isNegInf(i):
                        idx = SpecialValues.isNegInf(self.records[column])
                    else:
                        raise Exception("Unknown special value detected")
                else:
                    if SpecialValues.isEps(i):
                        idx = (idx) | (SpecialValues.isEps(self.records[column]))
                    elif SpecialValues.isNA(i):
                        idx = (idx) | (SpecialValues.isNA(self.records[column]))
                    elif SpecialValues.isUndef(i):
                        idx = (idx) | (SpecialValues.isUndef(self.records[column]))
                    elif SpecialValues.isPosInf(i):
                        idx = (idx) | (SpecialValues.isPosInf(self.records[column]))
                    elif SpecialValues.isNegInf(i):
                        idx = (idx) | (SpecialValues.isNegInf(self.records[column]))
                    else:
                        raise Exception("Unknown special value detected")

            return self.records.loc[idx, :]

    def countNA(self, columns: Optional[Union[str, List[str]]] = None) -> int:
        """
        Counts total number of SpecialValues.NA across columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to count special values in, by default None

        Returns
        -------
        Total number of SpecialValues.NA across columns
        """
        return self._countSpecialValues(SpecialValues.NA, columns=columns)

    def countEps(self, columns: Optional[Union[str, List[str]]] = None) -> int:
        """
        Counts total number of SpecialValues.EPS across columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to count special values in, by default None

        Returns
        -------
        Total number of SpecialValues.EPS across columns
        """
        return self._countSpecialValues(SpecialValues.EPS, columns=columns)

    def countUndef(self, columns: Optional[Union[str, List[str]]] = None) -> int:
        """
        Counts total number of SpecialValues.Undef across columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to count special values in, by default None

        Returns
        -------
        Total number of SpecialValues.Undef across columns
        """
        return self._countSpecialValues(SpecialValues.UNDEF, columns=columns)

    def countPosInf(self, columns: Optional[Union[str, List[str]]] = None) -> int:
        """
        Counts total number of SpecialValues.PosInf across columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to count special values in, by default None

        Returns
        -------
        Total number of SpecialValues.PosInf across columns
        """
        return self._countSpecialValues(SpecialValues.POSINF, columns=columns)

    def countNegInf(self, columns: Optional[Union[str, List[str]]] = None) -> int:
        """
        Counts total number of SpecialValues.NegInf across columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to count special values in, by default None

        Returns
        -------
        Total number of SpecialValues.NegInf across columns
        """
        return self._countSpecialValues(SpecialValues.NEGINF, columns=columns)

    def _countSpecialValues(self, special_value, columns):
        # ARG: special_value
        if not isinstance(special_value, float):
            raise TypeError("Argument 'float' must be type float")

        if not (
            SpecialValues.isEps(special_value)
            or SpecialValues.isNA(special_value)
            or SpecialValues.isUndef(special_value)
            or SpecialValues.isPosInf(special_value)
            or SpecialValues.isNegInf(special_value)
        ):
            return ValueError(
                "Argument 'special_value' is currently limited to one of the "
                "five special value constants defined as: "
                "SpecialValues.EPS SpecialValues.NA, SpecialValues.UNDEF, "
                "SpecialValues.POSINF, or SpecialValues.NEGINF"
            )

        # ARG: columns
        # set defaults
        if columns is None:
            if isinstance(self, abcs.ABCParameter):
                columns = "value"
            elif isinstance(self, (abcs.ABCVariable, abcs.ABCEquation)):
                columns = "level"
            else:
                raise Exception(f"Unsupported object type: {type(self)}")

        # checks
        if not isinstance(columns, (str, list)):
            raise TypeError(
                f"Argument 'columns' must be type str or list. User passed {type(columns)}."
            )

        if isinstance(columns, str):
            columns = [columns]

        if any(not isinstance(i, str) for i in columns):
            raise TypeError(f"Argument 'columns' must contain only type str.")

        if any(i not in self._attributes for i in columns):
            raise TypeError(
                f"Argument 'columns' must be a subset of the following: {self._attributes}"
            )

        if self.records is not None:
            if SpecialValues.isEps(special_value):
                return np.sum(SpecialValues.isEps(self.records[columns]))
            elif SpecialValues.isNA(special_value):
                return np.sum(SpecialValues.isNA(self.records[columns]))
            elif SpecialValues.isUndef(special_value):
                return np.sum(SpecialValues.isUndef(self.records[columns]))
            elif SpecialValues.isPosInf(special_value):
                return np.sum(SpecialValues.isPosInf(self.records[columns]))
            elif SpecialValues.isNegInf(special_value):
                return np.sum(SpecialValues.isNegInf(self.records[columns]))
            else:
                raise Exception("Unknown special value detected")

    def whereMax(self, column: Optional[str] = None) -> List[str]:
        """
        Find the domain entry of records with a maximum value (return first instance only)

        Parameters
        ----------
        column : str, optional
            Columns to find maximum values in, by default None

        Returns
        -------
        List[str]
            List of symbol names where maximum values exist
        """
        return self._whereMetric("max", column=column)

    def whereMaxAbs(self, column: Optional[str] = None) -> List[str]:
        """
        Find the domain entry of records with a maximum absolute value (return first instance only)

        Parameters
        ----------
        column : str, optional
            Columns to find maximum absolute values in, by default None

        Returns
        -------
        List[str]
            List of symbol names where maximum absolute values exist
        """

        return self._whereMetric("absmax", column=column)

    def whereMin(self, column: Optional[str] = None) -> List[str]:
        """
        Find the domain entry of records with a minimum value (return first instance only)

        Parameters
        ----------
        column : str, optional
            Columns to find minimum values in, by default None

        Returns
        -------
        List[str]
            List of symbol names where minimum values exist
        """

        return self._whereMetric("min", column=column)

    def _whereMetric(self, metric, column):
        # ARG: metric
        if not isinstance(metric, str):
            raise TypeError("Argument 'metric' must be type str")

        if metric not in [
            "max",
            "min",
            "absmax",
        ]:
            return ValueError(
                "Argument 'metric' is currently limited to str type 'max', 'min' or 'absmax'"
            )

        # ARG: columns

        # set defaults
        if column is None:
            if isinstance(self, abcs.ABCParameter):
                column = "value"
            elif isinstance(self, (abcs.ABCVariable, abcs.ABCEquation)):
                column = "level"
            else:
                raise Exception(f"Unsupported object type: {type(self)}")

        # checks
        if not isinstance(column, str):
            raise TypeError(
                f"Argument 'column' must be type str. User passed {type(column)}."
            )

        if column not in self._attributes:
            raise TypeError(
                f"Argument 'column' must be a one of the following: {self._attributes}"
            )

        if self.records is not None:
            dom = []
            if metric == "max":
                if self.dimension > 0:
                    try:
                        dom = list(
                            self.records[
                                self.records[column] == self.getMaxValue(column)
                            ].to_numpy()[0][: self.dimension]
                        )
                        return dom
                    except Exception as err:
                        return None

            if metric == "min":
                if self.dimension > 0:
                    try:
                        dom = list(
                            self.records[
                                self.records[column] == self.getMinValue(column)
                            ].to_numpy()[0][: self.dimension]
                        )
                        return dom
                    except:
                        return None

            if metric == "absmax":
                if self.dimension > 0:
                    try:
                        dom = list(
                            self.records[
                                self.records[column] == self.getMaxAbsValue(column)
                            ].to_numpy()[0][: self.dimension]
                        )
                        return dom
                    except:
                        return None

    def getMaxValue(self, columns: Optional[Union[str, List[str]]] = None) -> float:
        """
        Get the maximum value across chosen columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to find maximum values in, by default None

        Returns
        -------
        float
            Maximum value
        """
        return self._getMetric(metric="max", columns=columns)

    def getMinValue(self, columns: Optional[Union[str, List[str]]] = None) -> float:
        """
        Get the minimum value across chosen columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to find minimum values in, by default None

        Returns
        -------
        float
            Minimum value
        """
        return self._getMetric(metric="min", columns=columns)

    def getMeanValue(self, columns: Optional[Union[str, List[str]]] = None) -> float:
        """
        Get the mean value across chosen columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to find mean values in, by default None

        Returns
        -------
        float
            Mean value
        """
        return self._getMetric(metric="mean", columns=columns)

    def getMaxAbsValue(self, columns: Optional[Union[str, List[str]]] = None) -> float:
        """
        Get the maximum absolute value across chosen columns

        Parameters
        ----------
        columns : str | List[str], optional
            Columns to find maximum absolute values in, by default None

        Returns
        -------
        float
            Maximum absolute value
        """
        return self._getMetric(metric="absmax", columns=columns)

    def _getMetric(self, metric, columns):
        # ARG: metric
        if not isinstance(metric, str):
            raise TypeError("Argument 'metric' must be type str")

        if metric not in [
            "max",
            "min",
            "mean",
            "absmax",
        ]:
            return ValueError(
                "Argument 'metric' is currently limited to str type 'max', 'min' or 'mean', absmax"
            )

        # ARG: columns
        # set defaults
        if columns is None:
            if isinstance(self, abcs.ABCParameter):
                columns = "value"
            elif isinstance(self, (abcs.ABCVariable, abcs.ABCEquation)):
                columns = "level"

        # checks
        if not isinstance(columns, (str, list)):
            raise TypeError(
                f"Argument 'columns' must be type str or list. User passed {type(columns)}."
            )

        if isinstance(columns, str):
            columns = [columns]

        if any(not isinstance(i, str) for i in columns):
            raise TypeError(f"Argument 'columns' must contain only type str.")

        if any(i not in self._attributes for i in columns):
            raise TypeError(
                f"Argument 'columns' must be a subset of the following: {self._attributes}"
            )

        if self.records is not None:
            if metric == "max":
                return self.records[columns].max().max()
            elif metric == "min":
                return self.records[columns].min().min()
            elif metric == "mean":
                if not (
                    self.records[columns].min().min() == float("-inf")
                    and self.records[columns].max().max() == float("inf")
                ):
                    return self.records[columns].mean().mean()
                else:
                    return float("nan")
            elif metric == "absmax":
                return self.records[columns].abs().max().max()
