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

from __future__ import annotations
import copy
import itertools
import weakref
import pandas as pd
from pandas.api.types import CategoricalDtype, is_bool_dtype
from gams.core import gdx
from gams.transfer._abcs import ABCSet, ABCContainer
from gams.transfer._internals import generate_unique_labels
from gams.transfer.syms._mixins import (
    SAMixin,
    SAPVEMixin,
    SAUAMixin,
    SAUAPVEMixin,
    SPVEMixin,
)

from gams.transfer.syms._mixins.pivot import PivotSetMixin
from gams.transfer.syms._mixins.generateRecords import GenerateRecordsSetMixin
from gams.transfer.syms._mixins.equals import EqualsSetMixin
from typing import Any, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from gams.transfer import Container


class Set(
    SAMixin,
    SAPVEMixin,
    SAUAMixin,
    SAUAPVEMixin,
    SPVEMixin,
    PivotSetMixin,
    GenerateRecordsSetMixin,
    EqualsSetMixin,
    ABCSet,
):
    """
    Represents a Set symbol in GAMS.
    https://www.gams.com/latest/docs/UG_SetDefinition.html

    Parameters
    ----------
    container : Container
    name : str
    domain : list, optional
    is_singleton : bool, optional
    records : int | float | DataFrame, optional
    domain_forwarding : bool, optional
    description : str, optional

    Examples
    --------
    >>> import gams.transfer as gt
    >>> m = gt.Container()
    >>> i = gt.Set(m, "i", records=['i1','i2'])

    Attributes
    ----------
    container : Container object
        Container where the symbol exists
    description : str
        description of symbol
    dimension : int
        The dimension of symbol
    domain : List[Set | Alias | str]
        List of domains given either as string (* for universe set) or as reference to the Set/Alias object
    domain_forwarding : bool
        Flag that identifies if domain forwarding is enabled for the symbol
    domain_labels : List[str]
        The column headings for the records DataFrame
    domain_names : List[str]
        String version of domain names
    domain_type : str
        The state of domain links
    is_singleton : bool
        Flag that identifies if the the alias is singleton
    modified : bool
        Flag that identifies if the symbol has been modified
    name : str
        Name of the symbol
    number_records : int
        The number of symbol records
    records : DataFrame
        The main symbol records
    summary : dict
        A dict of only the metadata
    """

    @classmethod
    def _from_gams(
        cls,
        container,
        name,
        domain,
        is_singleton=False,
        records=None,
        description="",
    ):
        # create new symbol object
        obj = Set.__new__(cls)

        # set private properties directly
        obj._requires_state_check = False
        obj._container = weakref.proxy(container)
        obj._name = name
        obj._domain = domain
        obj._domain_forwarding = False
        obj._description = description

        obj._records = records
        obj._modified = True
        obj._is_singleton = is_singleton

        # typing
        if obj.is_singleton:
            obj._gams_type = gdx.GMS_DT_SET
            obj._gams_subtype = 1
        else:
            obj._gams_type = gdx.GMS_DT_SET
            obj._gams_subtype = 0

        # add to container
        obj._container.data.update({name: obj})
        obj._container._requires_state_check = True

        return obj

    def __new__(cls, *args, **kwargs):
        # fastpath
        if len(args) == len(kwargs) == 0:
            return object.__new__(cls)

        try:
            container = args[0]
        except IndexError:
            container = kwargs.get("container", None)

        try:
            name = args[1]
        except IndexError:
            name = kwargs.get("name", None)

        try:
            symobj = container[name]
        except (KeyError, IndexError, TypeError):
            symobj = None

        if symobj is None:
            return object.__new__(cls)
        else:
            if isinstance(symobj, cls):
                return symobj
            else:
                raise TypeError(
                    f"Cannot overwrite symbol '{symobj.name}' in container because it is not a {cls.__name__} object"
                )

    def __init__(
        self,
        container: "Container",
        name: str,
        domain: Optional[List[Union[Set, str]]] = None,
        is_singleton: bool = False,
        records: Optional[Any] = None,
        domain_forwarding: bool = False,
        description: str = "",
        uels_on_axes: bool = False,
    ):
        # domain handling
        if domain is None:
            domain = ["*"]

        if isinstance(domain, (Set, str)):
            domain = [domain]

        # does symbol exist
        has_symbol = False
        if isinstance(getattr(self, "container", None), ABCContainer):
            has_symbol = True

        if has_symbol:
            try:
                if not isinstance(self, Set):
                    raise TypeError(
                        f"Cannot overwrite symbol {self.name} in container"
                        " because it is not a Set object)"
                    )

                if any(
                    d1 != d2 for d1, d2 in itertools.zip_longest(self.domain, domain)
                ):
                    raise ValueError(
                        "Cannot overwrite symbol in container unless symbol"
                        " domains are equal"
                    )

                if self.is_singleton != is_singleton:
                    raise ValueError(
                        "Cannot overwrite symbol in container unless"
                        " 'is_singleton' is left unchanged"
                    )

                if self.domain_forwarding != domain_forwarding:
                    raise ValueError(
                        "Cannot overwrite symbol in container unless"
                        " 'domain_forwarding' is left unchanged"
                    )

            except ValueError as err:
                raise ValueError(err)

            except TypeError as err:
                raise TypeError(err)

            # reset some properties
            self._requires_state_check = True
            self.container._requires_state_check = True
            if description != "":
                self.description = description
            self.records = None
            self.modified = True

            # only set records if records are provided
            if records is not None:
                self.setRecords(records, uels_on_axes=uels_on_axes)

        else:
            # populate new symbol properties
            self._requires_state_check = True
            self.container = container
            self.container._requires_state_check = True
            self.name = name
            self.domain = domain
            self.domain_forwarding = domain_forwarding
            self.description = description
            self.records = None
            self.modified = True
            self.is_singleton = is_singleton

            # typing
            if self.is_singleton:
                self._gams_type = gdx.GMS_DT_SET
                self._gams_subtype = 1
            else:
                self._gams_type = gdx.GMS_DT_SET
                self._gams_subtype = 0

            # only set records if records are provided
            if records is not None:
                self.setRecords(records, uels_on_axes=uels_on_axes)

            # add to container
            container.data.update({name: self})

    def __repr__(self):
        return f"<Set `{self.name}` ({hex(id(self))})>"

    def __delitem__(self):
        # TODO: add in some functionality that might relax the symbols down to a different domain
        #       This function would mimic the <Container>.removeSymbols() method -- is more pythonic
        del self.container.data[self.name]

    @property
    def _attributes(self):
        return ["element_text"]

    @property
    def summary(self) -> dict:
        """
        Returns a dict of only the metadata

        Returns
        -------
        dict
            Outputs a dict of only the metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "is_singleton": self.is_singleton,
            "domain": self.domain_names,
            "domain_type": self.domain_type,
            "dimension": self.dimension,
            "number_records": self.number_records,
        }

    def toList(
        self, include_element_text=False
    ) -> Union[List[Union[str, tuple]], None]:
        """
        Convenience method to return symbol records as a python list

        Parameters
        ----------
        include_element_text : bool, optional
            If True, include the element text as tuples (record, element text).
            If False, return a list of records only.

        Returns
        -------
        list | None
            A list containing the records of the symbol, None if no record was assigned

        Examples
        --------
        >>> m = gt.Container()
        >>> i = gt.Set(m, "i", records=["new-york", "chicago", "topeka"])
        >>> print(i.toList())
        ['new-york', 'chicago', 'topeka']

        """
        from gams.transfer.syms._methods.toList import toListSet

        if not self.isValid():
            raise Exception(
                f"Cannot extract list because `{self.name}` is not a valid"
                f" symbol object. Use `{self.name}.isValid(verbose=True)` to"
                " debug."
            )
        return toListSet(self, include_element_text=include_element_text)

    @property
    def is_singleton(self) -> bool:
        """
        Whether a symbol is a singleton set

        Returns
        -------
        bool
            True if the symbol is a singleton set; False otherwise
        """
        return self._is_singleton

    @is_singleton.setter
    def is_singleton(self, is_singleton):
        if not isinstance(is_singleton, bool):
            raise TypeError("Argument 'is_singleton' must be type bool")

        # check to see if _is_singleton is being changed
        if getattr(self, "_is_singleton", None) != is_singleton:
            self._requires_state_check = True

            if isinstance(self.container, ABCContainer):
                self.container._requires_state_check = True

            self._is_singleton = is_singleton

    def setRecords(self, records: Any, uels_on_axes: bool = False) -> None:
        """
        main convenience method to set standard pandas.DataFrame formatted records.
        If uels_on_axes=True setRecords will assume that all domain information is contained in the axes of the pandas object – data will be flattened (if necessary).

        Parameters
        ----------
        records : Any
        uels_on_axes : bool, optional
        """
        if not isinstance(uels_on_axes, bool):
            raise TypeError("Argument 'uels_on_axes' must be type bool")

        if isinstance(records, pd.DataFrame):
            self._from_dataframe(records, uels_on_axes=uels_on_axes)

        elif isinstance(records, pd.Series):
            if uels_on_axes:
                self._from_series(records)
            else:
                if self.dimension != 1:
                    raise Exception(
                        "Dimensionality of data (1) is inconsistent "
                        f"with domain specification ({self.dimension})"
                    )

                records = pd.DataFrame(records)
                r, c = records.shape

                if c == self.dimension:
                    records = records.assign(element_text="")

                records.columns = (
                    generate_unique_labels(self.domain_names) + self._attributes
                )

                self._from_dataframe(records)

        else:
            self._from_else(records)

    def _from_series(self, records: pd.Series) -> None:
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

        # else:
        dim = _get_implied_dimension_from_axes(records)
        if dim != self.dimension:
            raise Exception(
                f"Dimensionality of data ({dim}) is inconsistent "
                f"with domain specification ({self.dimension})"
            )

        # flatten and convert to categorical
        records = _flatten_and_convert(records)

        # reset columns
        records.columns = generate_unique_labels(self.domain_names) + self._attributes

        # fill any missing element_text with empty str and convert everything to str
        records.isetitem(-1, records.iloc[:, -1].astype(object))
        records.iloc[records.iloc[:, -1].isna(), -1] = ""
        records.isetitem(-1, records.iloc[:, -1].astype(str))

        # set records
        self.records = records

    def _from_dataframe(
        self, records: pd.DataFrame, uels_on_axes: bool = False
    ) -> None:
        if uels_on_axes:
            if is_bool_dtype(records.to_numpy().dtype):
                self._from_table_dataframe(records)

            else:
                if any(
                    not is_bool_dtype(dtype)
                    for dtype in records.convert_dtypes().dtypes
                ):
                    raise TypeError(
                        "Encountered records that could not successfully be"
                        " converted to type bool. All columns must be type"
                        " bool when `uels_on_axes=True`"
                    )

                else:
                    self._from_table_dataframe(records.convert_dtypes())
        else:
            self._from_else(records)

    def _from_table_dataframe(self, records: pd.DataFrame) -> None:
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

        # check dimensionality of data
        dim = _get_implied_dimension_from_axes(records)
        if dim != self.dimension:
            raise Exception(
                f"Dimensionality of table ({dim}) is inconsistent "
                f"with set domain specification ({self.dimension})"
            )

        # flatten and convert to categorical
        records = _flatten_and_convert(records)

        # drop records and reset_index
        records.drop(index=records[records.iloc[:, -1] == False].index, inplace=True)
        records.drop(columns=records.columns[-1], inplace=True)
        records.reset_index(drop=True, inplace=True)

        # add in element_text column
        records["element_text"] = ""

        # set columns names
        records.columns = generate_unique_labels(self.domain_names) + self._attributes

        # set records
        self.records = records

    def _from_else(self, records: Any) -> None:
        from_dataframe = False

        if isinstance(records, str):
            records = [records]

        # check dimensionality of data
        try:
            # create a deep copy of all passed DataFrames
            if isinstance(records, pd.DataFrame):
                records = pd.DataFrame(copy.deepcopy(records))
                from_dataframe = True
            else:
                records = pd.DataFrame(records)
        except Exception as err:
            raise Exception(
                "Data structure passed as argument 'records' could not be"
                " successfully converted into a pandas DataFrame (reason:"
                f" {err})."
            )

        # check dimensionality
        r, c = records.shape
        if c == self.dimension:
            records = records.assign(element_text="")

        r, c = records.shape
        if c - 1 != self.dimension:
            raise Exception(
                f"Dimensionality of records ({c - 1}) is inconsistent "
                f"with set domain specification ({self.dimension})"
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
                # convert data to str and strip trailing white-space from data
                records.isetitem(
                    i,
                    records.iloc[:, i]
                    .astype(str)
                    .map(str.rstrip)
                    .astype(CategoricalDtype(categories=new_cats, ordered=is_ordered)),
                )

            else:
                # only need to rename the categories
                records.isetitem(
                    i,
                    records.iloc[:, i].cat.rename_categories(new_cats),
                )

        # set column names
        if from_dataframe:
            records.columns = (
                generate_unique_labels(records.columns[: self.dimension].tolist())
                + self._attributes
            )
        else:
            records.columns = (
                generate_unique_labels(self.domain_names) + self._attributes
            )

        # fill any missing element_text with empty str and convert everything to str
        records.isetitem(-1, records.iloc[:, -1].astype(object))
        records.iloc[records.iloc[:, -1].isna(), -1] = ""
        records.isetitem(-1, records.iloc[:, -1].astype(str))

        # set records
        self.records = records
