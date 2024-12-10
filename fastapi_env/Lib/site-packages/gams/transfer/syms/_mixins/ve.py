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

import copy
import pandas as pd
from pandas.api.types import CategoricalDtype, infer_dtype
import numpy as np
from typing import Optional
from gams.transfer._internals import (
    generate_unique_labels,
    DomainStatus,
    cartesian_product,
    EPS,
    UNDEF,
    NA,
    SpecialValues,
)


class VEMixin:
    @property
    def _attributes(self):
        return ["level", "marginal", "lower", "upper", "scale"]

    @property
    def type(self):
        return self._type

    @property
    def summary(self):
        """Summary of the symbol"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "domain": self.domain_names,
            "domain_type": self.domain_type,
            "dimension": self.dimension,
            "number_records": self.number_records,
        }

    def dropDefaults(self) -> None:
        """
        Drop records that are set to GAMS default records (check .default_records property for values)
        """
        mask = np.all(
            self.records[self._attributes]
            == np.array(list(self.default_records.values())),
            axis=1,
        ) & ~np.any(
            (self.records[self._attributes] == 0.0)
            & SpecialValues.isEps(self.records[self._attributes]),
            axis=1,
        )
        self.records = self.records[~mask].reset_index(drop=True)

    def dropNA(self) -> None:
        """
        Drop records from the symbol that are GAMS NA
        """
        mask = SpecialValues.isNA(self.records[self._attributes]).any(axis=1)
        self.records = self.records[~mask].reset_index(drop=True)

    def dropUndef(self) -> None:
        """
        Drop records from the symbol that are GAMS Undef
        """
        mask = SpecialValues.isUndef(self.records[self._attributes]).any(axis=1)
        self.records = self.records[~mask].reset_index(drop=True)

    def dropEps(self) -> None:
        """
        Drop records from the symbol that are GAMS EPS (zero 0.0 records will be retained)
        """
        mask = SpecialValues.isEps(self.records[self._attributes]).any(axis=1)
        self.records = self.records[~mask].reset_index(drop=True)

    def dropMissing(self) -> None:
        """
        Drop records from the symbol that are NaN (includes both NA and Undef special values)
        """
        mask = pd.isna(self.records[self._attributes]).any(axis=1)
        self.records = self.records[~mask].reset_index(drop=True)

    def toValue(self, column: Optional[str] = None) -> float:
        """
        Convenience method to return symbol records as a Python float. Only possible with scalar symbols

        Parameters
        ----------
        column : str, optional
            Attribute can be specified with column argument, by default None

        Returns
        -------
        float
            Value of the symbol
        """
        from gams.transfer.syms._methods.toValue import toValueVariableEquation

        if not self.isValid():
            raise Exception(
                f"Cannot extract value because `{self.name}` is not a valid symbol object. "
                f"Use `{self.name}.isValid(verbose=True)` to debug."
            )

        return toValueVariableEquation(self, column=column)

    def toList(self, columns: Optional[str] = None) -> list:
        """
        Convenience method to return symbol records as a Python list

        Parameters
        ----------
        columns : str, optional
            Controls which attributes to include in the list, by default None

        Returns
        -------
        list
            Records as a Python list
        """
        from gams.transfer.syms._methods.toList import toListVariableEquation

        if not self.isValid():
            raise Exception(
                f"Cannot extract list because `{self.name}` is not a valid symbol object. "
                f"Use `{self.name}.isValid(verbose=True)` to debug."
            )
        return toListVariableEquation(self, columns=columns)

    def toDict(
        self, columns: Optional[str] = None, orient: Optional[str] = None
    ) -> dict:
        """
        Convenience method to return symbol records as a Python dictionary

        Parameters
        ----------
        columns : str, optional
            Controls which attributes to include in the dict, by default None
        orient : str, optional
            Orient can take values natural or columns and will control the shape of the dict. Must use orient="columns" if attempting to set symbol records with setRecords, by default None

        Returns
        -------
        dict
            Records as a Python dictionary
        """
        from gams.transfer.syms._methods.toDict import toDictVariableEquation

        if not self.isValid():
            raise Exception(
                f"Cannot extract dict because `{self.name}` is not a valid symbol object. "
                f"Use `{self.name}.isValid(verbose=True)` to debug."
            )

        return toDictVariableEquation(self, columns=columns, orient=orient)

    def setRecords(self, records, uels_on_axes: bool = False) -> None:
        """
        Main convenience method to set standard pandas.DataFrame formatted records

        Parameters
        ----------
        records : Any
            Records to set for the symbol
        uels_on_axes : bool, optional
            If True, setRecords will assume that all domain information is contained in the axes of the pandas object – data will be flattened (if necessary), by default False
        """
        if isinstance(records, (int, float)):
            self._from_int_float(records)

        elif isinstance(records, np.ndarray):
            self._from_ndarray(records)

        elif isinstance(records, pd.DataFrame):
            self._from_dataframe(records, uels_on_axes=uels_on_axes)

        elif isinstance(records, pd.Series):
            self._from_series(records)

        elif isinstance(records, dict):
            self._from_dict(records)

        else:
            self._from_else(records)

    def _from_dict(self, records):
        if all(
            i in self._attributes and isinstance(records[i], (np.ndarray, int, float))
            for i in records.keys()
        ):
            self._from_dict_of_arrays(records)
        else:
            self._from_else(records)

    def _from_series(self, records):
        from gams.transfer.syms._methods.tables import (
            _assert_axes_no_nans,
            _get_implied_dimension_from_axes,
            _flatten_and_convert,
        )

        records = copy.deepcopy(records)

        # check if index has NaNs
        try:
            _assert_axes_no_nans(records)
        except Exception as err:
            raise err

        # check indices for variable/equation attributes
        n_idx = self._position_of_attributes(records)
        if sum(n_idx) > 1:
            raise Exception(
                "Detected symbol attributes in more than one level of a MultiIndex object"
            )

        # special things if scalar
        if self.is_scalar:
            if sum(n_idx):
                recs = pd.DataFrame(columns=records.index.tolist())
                for i in records.index:
                    recs.loc[0, i] = records[i]
                self._from_dataframe(recs)
            elif records.size == 1:
                records = pd.DataFrame(records, columns=["level"])
                self._from_dataframe(records)
            else:
                raise Exception(
                    f"Attempting to set records for a scalar symbol but records.size > 1. "
                    "pandas.Series must have size exactly = 1 before setting records. "
                    "(Note: pandas.Series.index is ignored for scalar symbols)"
                )
        else:
            # check dimensionality of data
            dim = _get_implied_dimension_from_axes(records) - sum(n_idx)
            if dim != self.dimension:
                raise Exception(
                    f"Dimensionality of table ({dim}) is inconsistent "
                    f"with symbol domain specification ({self.dimension})"
                )

            # flatten and convert to categorical
            records = _flatten_and_convert(records)

            # remap special values (str -> float)
            records = self._remap_str_special_values(records)

            # unstack attributes column (if provided)
            if any(n_idx):
                attr = records.iloc[:, n_idx.index(True)].cat.categories.tolist()
                records = (
                    records.set_index(records.columns.tolist()[:-1])
                    .unstack(n_idx.index(True))
                    .reset_index(drop=False)
                )
                records.columns = ["*"] * self.dimension + attr
            else:
                records.columns = ["*"] * self.dimension + ["level"]

            self._from_dataframe(records)

    def _from_dataframe(self, records, uels_on_axes=False):
        if self.is_scalar:
            self._from_flat_dataframe(records)

        else:
            if uels_on_axes:
                self._from_table_dataframe(records)
            else:
                self._from_flat_dataframe(records)

    def _from_flat_dataframe(self, records):
        records = pd.DataFrame(copy.deepcopy(records))
        usr_cols = list(records.columns)

        # FILL DEFAULT VALUES
        # fill in columns that might not have been supplied
        if set(records[self.dimension :].columns) != set(self._attributes):
            for i in set(self._attributes) - set(records[self.dimension :].columns):
                records[i] = self.default_records[i]

        # check dimensionality
        r, c = records.shape
        if len(records.columns) != self.dimension + len(self._attributes):
            raise Exception(
                f"Dimensionality of records "
                f"({c - len(self._attributes)}) "
                "is inconsistent w/ variable domain specification "
                f"({self.dimension}), "
                "must resolve before records can be added.\n\nNOTE: "
                "columns not named "
                f"{self._attributes} will be interpreted as domain columns, "
                "check that the DataFrame conforms to the required "
                "notation.\nUser passed DataFrame with columns: "
                f"{usr_cols}"
            )

        if self.is_scalar and r > 1:
            raise Exception(
                f"Attempting to set {r} records for a scalar symbol. "
                f"Must define a domain for symbol `{self.name}` in order to set multiple records."
            )

        # reorder columns to fit standard format
        records = pd.concat(
            [records.iloc[:, : self.dimension], records[self._attributes]], axis=1
        )

        # keep user defined categories if provided
        for i in range(self.dimension):
            # create categorical
            if not isinstance(records.iloc[:, i].dtype, CategoricalDtype):
                records.isetitem(
                    i,
                    records.iloc[:, i].astype(
                        CategoricalDtype(
                            categories=records.iloc[:, i].unique(),
                            ordered=True,
                        )
                    ),
                )

            # capture user categories
            old_cats = records.iloc[:, i].cat.categories.tolist()
            is_ordered = records.iloc[:, i].cat.ordered

            # convert any non-str categories to str, strip trailing white-space and de-dup
            new_cats = list(dict.fromkeys(list(map(str.rstrip, map(str, old_cats)))))

            # if categories are not unique after strip then need to remake the categorical
            if len(old_cats) != len(new_cats):
                # convert data to str, strip white-space and make categorical
                records.isetitem(
                    i,
                    records.iloc[:, i]
                    .astype(str)
                    .map(str.rstrip)
                    .astype(CategoricalDtype(categories=new_cats, ordered=is_ordered)),
                )

            else:
                # only need to rename the categories
                records.isetitem(i, records.iloc[:, i].cat.rename_categories(new_cats))

        # remap special values (str -> float)
        records = self._remap_str_special_values(records)

        # must be able to convert data columns to type float
        for i in records.columns[self.dimension :]:
            records[i] = records[i].astype(float)

        # reset column names
        records.columns = (
            generate_unique_labels(records.columns[: self.dimension].tolist())
            + self._attributes
        )

        # set records
        self.records = records

    def _from_table_dataframe(self, records):
        from gams.transfer.syms._methods.tables import (
            _assert_axes_no_nans,
            _get_implied_dimension_from_axes,
            _flatten_and_convert,
        )

        records = pd.DataFrame(copy.deepcopy(records))

        # check if index has NaNs
        try:
            _assert_axes_no_nans(records)
        except Exception as err:
            raise err

        # check indices for variable/equation attributes
        n_idx = self._position_of_attributes(records)

        if sum(n_idx) > 1:
            raise Exception(
                "Detected symbol attributes in more than one DataFrame index.  "
                "All symbol attributes must be indexed in exactly one index object"
                "(or column object) or within exactly one level of a MultiIndex object"
            )

        # check dimensionality of data
        dim = _get_implied_dimension_from_axes(records) - sum(n_idx)
        if dim != self.dimension:
            raise Exception(
                f"Dimensionality of table ({dim}) is inconsistent "
                f"with symbol domain specification ({self.dimension})"
            )

        # flatten and convert to categorical
        records = _flatten_and_convert(records)

        # remap special values (str -> float)
        records = self._remap_str_special_values(records)

        # unstack attributes column (if provided)
        if any(n_idx):
            attr = records.iloc[:, n_idx.index(True)].cat.categories.tolist()
            records = (
                records.set_index(records.columns.tolist()[:-1])
                .unstack(n_idx.index(True))
                .reset_index(drop=False)
            )
            records.columns = ["*"] * self.dimension + attr

        else:
            records.columns = ["*"] * self.dimension + ["level"]

        # FILL DEFAULT VALUES
        # fill in columns that might not have been supplied
        if set(records.columns) != set(self._attributes):
            for i in set(self._attributes) - set(records.columns):
                records[i] = self.default_records[i]

        # reorder columns to fit standard format
        records = pd.concat(
            [records.iloc[:, : self.dimension], records[self._attributes]], axis=1
        )

        # convert data column to type float
        for i in range(self.dimension, self.dimension + len(self._attributes)):
            if not isinstance(records.iloc[:, i].dtype, float):
                records.isetitem(i, records.iloc[:, i].astype(float))

        # reset column names
        records.columns = generate_unique_labels(self.domain_names) + self._attributes

        # set records
        self.records = records

    def _from_int_float(self, records):
        if not self.is_scalar:
            raise Exception(
                "Attempting to set a record with a scalar value, however the "
                "symbol is not currently defined as a scalar (i.e., <symbol>.is_scalar == False)"
            )

        # note we do not drop zeros when setting
        self._from_flat_dataframe(pd.DataFrame([records], columns=["level"]))

    def _from_ndarray(self, records):
        records = {"level": records}
        self._from_dict_of_arrays(records)

    def _from_dict_of_arrays(self, records):
        # check all keys in records dict
        if any(i not in self._attributes for i in records.keys()):
            raise Exception(
                f"Unrecognized variable attribute detected in `records`. "
                f"Attributes must be {self._attributes}, user passed "
                f"dict keys: {list(records.keys())}."
            )

        # convert all values to numpy array (float dtype)
        for k, v in records.items():
            try:
                records[k] = np.array(v, dtype=float)
            except Exception as err:
                raise Exception(
                    f"Could not successfully convert `{k}` "
                    f"records to a numpy array (dtype=float), reason: {err}."
                )

        # user flexibility for (n,1) and (1,n) arrays (auto reshape)
        for k, arr in records.items():
            if self.dimension == 1 and (
                arr.shape == (1, arr.size) or arr.shape == (arr.size, 1)
            ):
                records[k] = arr.reshape((arr.size,))

        # check dimension of array and symbol
        for k, arr in records.items():
            if arr.ndim != self.dimension:
                raise Exception(
                    f"Attempting to set `{k}` records for a {self.dimension}-dimensional "
                    f"symbol with a numpy array that is {arr.ndim}-dimensional "
                    "-- array reshape necessary. (Note: transfer will auto "
                    "reshape array if symbol is 1D and array is either (1,n) or (n,1))"
                )

        # all records arrays must have the same size
        shapes = [arr.shape for k, arr in records.items()]
        if any(i != shapes[0] for i in shapes):
            raise Exception(
                "Arrays passed into `records` do not have the same shape -- array reshape necessary"
            )

        # symbol must have regular domain_type if not a scalar
        if self.dimension > 0 and self._domain_status is not DomainStatus.regular:
            raise Exception(
                "Data conversion for non-scalar array (i.e., matrix) format into "
                "records is only possible for symbols defined over valid domain set objects "
                "(i.e., has a 'regular' domain type). \n"
                "Current symbol specifics\n"
                "------------------------------\n"
                f"Domain type: '{self.domain_type}'\n"
                f"Symbol domain: {self.domain}\n"
                f"Symbol dimension: {self.dimension}\n"
            )

        # all domain sets have to be valid
        for i in self.domain:
            if not i.isValid():
                raise Exception(
                    f"Domain set `{i.name}` is invalid and cannot "
                    "be used to convert array-to-records. "
                    "Use `<symbol>.isValid(verbose=True)` to debug this "
                    "domain set symbol before proceeding."
                )

        # make sure all arrays have the proper (anticipated) shape
        for k, arr in records.items():
            if arr.shape != self.shape:
                raise Exception(
                    f"User passed array with shape `{arr.shape}` but anticipated "
                    f"shape was `{self.shape}` based "
                    "on domain set information -- "
                    "must reconcile before array-to-records conversion is possible."
                )

        # create array of codes
        codes = [np.arange(len(d.getUELs(ignore_unused=True))) for d in self.domain]

        # create dataframe
        if self.is_scalar:
            df = pd.DataFrame(index=[0], columns=list(records.keys()))
        else:
            df = pd.DataFrame(cartesian_product(*tuple(codes)))

            # create categoricals
            for n, d in enumerate(self.domain):
                dtype = CategoricalDtype(
                    categories=d.records.iloc[:, 0].cat.categories,
                    ordered=d.records.iloc[:, 0].cat.ordered,
                )
                df.isetitem(
                    n, pd.Categorical.from_codes(codes=df.iloc[:, n], dtype=dtype)
                )

        # insert matrix elements
        for i in records.keys():
            df[i] = records[i].reshape(-1, 1)

        # drop zeros and reset index
        df = self._filter_zero_records(df)

        # FILL DEFAULT VALUES
        # fill in columns that might not have been supplied
        if set(records.keys()) != set(self._attributes):
            for i in set(self._attributes) - set(records.keys()):
                df[i] = self.default_records[i]

        # reorder columns to fit standard format
        df = pd.concat([df.iloc[:, : self.dimension], df[self._attributes]], axis=1)

        # reset column names
        df.columns = generate_unique_labels(self.domain_names) + self._attributes

        # set records
        self.records = df

    def _from_else(self, records):
        try:
            records = pd.DataFrame(records)
        except Exception as err:
            raise Exception(
                "Data structure passed as argument 'records' could not be "
                f"successfully converted into a pandas DataFrame (reason: {err})."
            )
        usr_cols = list(records.columns)

        # FILL DEFAULT VALUES
        # fill in columns that might not have been supplied
        if set(records[self.dimension :].columns) != set(self._attributes):
            for i in set(self._attributes) - set(records[self.dimension :].columns):
                records[i] = self.default_records[i]

        # check dimensionality
        r, c = records.shape
        if len(records.columns) != self.dimension + len(self._attributes):
            raise Exception(
                f"Dimensionality of records "
                f"({c - len(self._attributes)}) "
                "is inconsistent w/ variable domain specification "
                f"({self.dimension}), "
                "must resolve before records can be added.\n\nNOTE: "
                "columns not named "
                f"{self._attributes} will be interpreted as domain columns, "
                "check that the DataFrame conforms to the required "
                "notation.\nUser passed DataFrame with columns: "
                f"{usr_cols}"
            )

        if self.is_scalar and r > 1:
            raise Exception(
                f"Attempting to set {r} records for a scalar symbol. "
                f"Must define a domain for symbol `{self.name}` in order to set multiple records."
            )

        # reorder columns to fit standard format
        records = pd.concat(
            [records.iloc[:, : self.dimension], records[self._attributes]], axis=1
        )

        # keep user defined categories if provided
        for i in range(self.dimension):
            # create categorical
            if not isinstance(records.iloc[:, i].dtype, CategoricalDtype):
                records.isetitem(
                    i,
                    records.iloc[:, i].astype(
                        CategoricalDtype(
                            categories=records.iloc[:, i].unique(),
                            ordered=True,
                        )
                    ),
                )

            # capture user categories
            old_cats = records.iloc[:, i].cat.categories.tolist()
            is_ordered = records.iloc[:, i].cat.ordered

            # convert any non-str categories to str, strip trailing white-space and de-dup
            new_cats = list(dict.fromkeys(list(map(str.rstrip, map(str, old_cats)))))

            # if categories are not unique after strip then need to remake the categorical
            if len(old_cats) != len(new_cats):
                # convert data to str, strip white-space and make categorical
                records.isetitem(
                    i,
                    records.iloc[:, i]
                    .astype(str)
                    .map(str.rstrip)
                    .astype(CategoricalDtype(categories=new_cats, ordered=is_ordered)),
                )

            else:
                # only need to rename the categories
                records.isetitem(i, records.iloc[:, i].cat.rename_categories(new_cats))

        # remap special values (str -> float)
        records = self._remap_str_special_values(records)

        # must be able to convert data columns to type float
        for i in records.columns[self.dimension :]:
            records[i] = records[i].astype(float)

        # reset column names
        records.columns = generate_unique_labels(self.domain_names) + self._attributes

        # set records
        self.records = records

    def toSparseCoo(self, column: str = "level") -> Optional["coo_matrix"]:
        """
        Convert column to a sparse COOrdinate numpy.array format

        Parameters
        ----------
        column : str, optional
            The column to convert, by default "level"

        Returns
        -------
        coo_matrix, optional
            A column in coo_matrix format
        """
        from scipy.sparse import coo_matrix

        if not isinstance(column, str):
            raise TypeError("Argument 'column' must be type str")

        if column not in self._attributes:
            raise TypeError(
                f"Argument 'column' must be one of the following: {self._attributes}"
            )

        if not self.isValid():
            raise Exception(
                "Cannot create sparse array (i.e., coo_matrix) because symbol "
                "is invalid -- use `<symbol>.isValid(verbose=True)` to debug symbol state."
            )
        else:
            if self._domain_status is DomainStatus.regular:
                if self.hasDomainViolations():
                    raise Exception(
                        "Cannot create sparse array because there are domain violations "
                        "(i.e., UELs in the symbol are not a subset of UELs contained in domain sets)."
                    )

            if self.records is not None:
                if self.is_scalar:
                    row = [0]
                    col = [0]
                    m = 1
                    n = 1

                elif self.dimension == 1:
                    if self._domain_status is DomainStatus.regular:
                        col = (
                            self.records.iloc[:, 0]
                            .map(self.domain[0]._getUELCodes(0, ignore_unused=True))
                            .to_numpy(dtype=int)
                        )
                    else:
                        col = self.records.iloc[:, 0].cat.codes.to_numpy(dtype=int)

                    row = np.zeros(len(col), dtype=int)
                    m, *n = self.shape
                    assert n == []
                    n = m
                    m = 1

                elif self.dimension == 2:
                    if self._domain_status is DomainStatus.regular:
                        row = (
                            self.records.iloc[:, 0]
                            .map(self.domain[0]._getUELCodes(0, ignore_unused=True))
                            .to_numpy(dtype=int)
                        )
                        col = (
                            self.records.iloc[:, 1]
                            .map(self.domain[1]._getUELCodes(0, ignore_unused=True))
                            .to_numpy(dtype=int)
                        )
                    else:
                        row = self.records.iloc[:, 0].cat.codes.to_numpy(dtype=int)
                        col = self.records.iloc[:, 1].cat.codes.to_numpy(dtype=int)

                    m, n = self.shape

                else:
                    raise Exception(
                        "Sparse coo_matrix formats are only "
                        "available for data that has dimension <= 2"
                    )

                return coo_matrix(
                    (
                        self.records.loc[:, column].to_numpy(dtype=float),
                        (row, col),
                    ),
                    shape=(m, n),
                    dtype=float,
                )
            else:
                return None

    def toDense(self, column: str = "level") -> Optional[np.ndarray]:
        """
        Convert column to a dense numpy.array format

        Parameters
        ----------
        column : str, optional
            The column to convert, by default "level"

        Returns
        -------
        np.ndarray, optional
            A column to a dense numpy.array format
        """
        if not isinstance(column, str):
            raise TypeError(f"Argument 'column' must be type str")

        if column not in self._attributes:
            raise TypeError(
                f"Argument 'column' must be one of the following: {self._attributes}"
            )

        if not self.isValid():
            raise Exception(
                "Cannot create dense array (i.e., matrix) format because symbol "
                "is invalid -- use `<symbol>.isValid(verbose=True)` to debug symbol state."
            )
        else:
            if self.records is not None:
                if self.is_scalar:
                    return self.records.loc[:, column].to_numpy(dtype=float)[0]

                else:
                    #
                    #
                    # checks
                    if self.domain_type == "regular":
                        if self.hasDomainViolations():
                            raise Exception(
                                "Cannot create dense array because there are domain violations "
                                "(i.e., UELs in the symbol are not a subset of UELs contained in domain sets)."
                            )

                        # check order of domain UELs in categorical and order of domain UELs in data
                        for symobj in self.domain:
                            data_cats = symobj.records.iloc[:, 0].unique().tolist()
                            cats = symobj.records.iloc[:, 0].cat.categories.tolist()

                            if data_cats != cats[: len(data_cats)]:
                                raise Exception(
                                    f"`toDense` requires that UEL data order of domain set `{symobj.name}` must be "
                                    "equal be equal to UEL category order (i.e., the order that set elements "
                                    "appear in rows of the dataframe and the order set elements are specified by the categorical). "
                                    "Users can efficiently reorder their domain set UELs to data order with "
                                    "the `reorderUELs()` method (no arguments) -- preexisting unused categories "
                                    "will be appended (maintaining their order)."
                                )
                    else:
                        # check order of domain UELs in categorical and order of domain UELs in data
                        for n in range(self.dimension):
                            # check if any invalid codes
                            if any(
                                code == -1 for code in self.records.iloc[:, n].cat.codes
                            ):
                                raise Exception(
                                    f"Invalid category detected in dimension `{n}` (code == -1), "
                                    "cannot create array until all categories are properly resolved"
                                )

                            data_cats = self.records.iloc[:, n].unique().tolist()
                            cats = self.records.iloc[:, n].cat.categories.tolist()

                            if data_cats != cats[: len(data_cats)]:
                                raise Exception(
                                    f"`toDense` requires (for 'relaxed' symbols) that UEL data order must be "
                                    "equal be equal to UEL category order (i.e., the order that set elements "
                                    "appear in rows of the dataframe and the order set elements are specified by the categorical). "
                                    "Users can efficiently reorder UELs to data order with "
                                    "the `reorderUELs()` method (no arguments) -- preexisting unused categories "
                                    "will be appended (maintaining their order)."
                                )

                    #
                    #
                    # create indexing scheme
                    if self.domain_type == "regular":
                        idx = [
                            self.records.iloc[:, n]
                            .map(domainobj._getUELCodes(0, ignore_unused=True))
                            .to_numpy(dtype=int)
                            for n, domainobj in enumerate(self.domain)
                        ]

                    else:
                        idx = [
                            self.records.iloc[:, n].cat.codes.to_numpy(dtype=int)
                            for n, domainobj in enumerate(self.domain)
                        ]

                    # fill the dense array
                    a = np.zeros(self.shape)
                    val = self.records.loc[:, column].to_numpy(dtype=float)
                    a[tuple(idx)] = val

                    return a
            else:
                return None

    def _position_of_attributes(self, records):
        idx = []
        for axis in records.axes:
            for n in range(axis.nlevels):
                if isinstance(axis, pd.MultiIndex):
                    if all(
                        str(i).casefold() in self._attributes for i in axis.levels[n]
                    ):
                        idx.append(True)
                    else:
                        idx.append(False)

                else:
                    if all(str(i).casefold() in self._attributes for i in axis):
                        idx.append(True)
                    else:
                        idx.append(False)
        return idx

    def _remap_str_special_values(self, records):
        # convert str "eps", "na", & "undef" special value strings to float equivalents
        for i in records.columns[self.dimension :]:
            if infer_dtype(records[i]) not in [
                "integer",
                "floating",
                "mixed-integer-float",
            ]:
                idx = records.loc[:, i].isin(EPS)
                if idx.any():
                    records.loc[records[idx].index, i] = SpecialValues.EPS

                idx = records.loc[:, i].isin(UNDEF)
                if idx.any():
                    records.loc[records[idx].index, i] = SpecialValues.UNDEF

                idx = records.loc[:, i].isin(NA)
                if idx.any():
                    records.loc[records[idx].index, i] = SpecialValues.NA

        return records

    def _filter_zero_records(self, records):
        idx = records[records[records.columns[self.dimension :]].eq(0).all(1)].index
        eps_idx = records[
            SpecialValues.isEps(records[records.columns[self.dimension :]]).any(1)
        ].index
        idx = idx.difference(eps_idx)

        return records.drop(idx).reset_index(drop=True)
