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

import pandas as pd
import weakref
from gams.core import gdx
from gams.transfer._abcs import (
    ABCSet,
    ABCAlias,
    ABCUniverseAlias,
    ABCContainer,
)
from gams.transfer.syms._mixins import SAMixin, SAPVEMixin, SAUAMixin, SAUAPVEMixin
from typing import TYPE_CHECKING, Union, Optional, List, Any


if TYPE_CHECKING:
    from gams.transfer import Container
    from gams.transfer import Set
    from gams.transfer._internals import DomainViolation


class Alias(SAMixin, SAPVEMixin, SAUAMixin, SAUAPVEMixin, ABCAlias):
    """
    Represents an Alias symbol in GAMS.
    https://www.gams.com/latest/docs/UG_SetDefinition.html#UG_SetDefinition_TheAliasStatementMultipleNamesForASet

    Parameters
    ----------
    container : Container
        The container to which the alias belongs.
    name : str
        Name of the alias.
    alias_with : Set
        The set with which the alias will share its data.

    Examples
    --------
    >>> import gams.transfer as gt
    >>> m = gt.Container()
    >>> i = gt.Set(m, "i")
    >>> j = gt.Alias(m, "j", i)

    Attributes
    ----------
    alias_with : Set Object
        Aliased object
    container : Container object
        Container where the symbol exists
    description : str
        description of symbol
    dimension : int
        The dimension of symbol
    domain : List[Set | Alias | str]
        List of domains given either as string (* for universe set) or as reference to the Set/Alias object
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
    def _from_gams(cls, container, name, alias_with):
        # create new symbol object
        obj = Alias.__new__(cls)

        # set private properties directly
        obj._requires_state_check = False
        obj._container = weakref.proxy(container)
        obj._name = name
        obj._alias_with = alias_with
        obj._modified = True

        # typing
        obj._gams_type = gdx.GMS_DT_ALIAS
        obj._gams_subtype = 1

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

    def __init__(self, container: "Container", name: str, alias_with: "Set") -> None:
        # does symbol exist
        has_symbol = False
        if isinstance(getattr(self, "container", None), ABCContainer):
            has_symbol = True

        if has_symbol:
            # reset some properties
            self._requires_state_check = True
            self.container._requires_state_check = True
            self.modified = True
            self.alias_with = alias_with

        else:
            # populate new symbol properties
            self._requires_state_check = True
            self.container = container
            self.name = name
            self.modified = True
            self.alias_with = alias_with
            self._gams_type = gdx.GMS_DT_ALIAS
            self._gams_subtype = 1
            container.data.update({name: self})

    def __repr__(self):
        return f"<Alias `{self.name}` ({hex(id(self))})>"

    def __delitem__(self):
        # TODO: add in some functionality that might relax the symbols down to a different domain
        #       This function would mimic the <Container>.removeSymbols() method -- is more pythonic
        del self.container.data[self.name]

    def equals(
        self,
        other: Union["Set", "Alias"],
        check_uels: bool = True,
        check_element_text: bool = True,
        check_meta_data: bool = True,
        verbose: bool = False,
    ) -> bool:
        """
        Used to compare the symbol to another symbol.

        Parameters
        ----------
        other : Set or Alias
            The other symbol (Set or Alias) to compare with the current alias.
        check_uels : bool, optional
            If True, check both used and unused UELs and confirm same order, otherwise only check used UELs in data and do not check UEL order.
        check_element_text : bool, optional
            If True, check that all set elements have the same descriptive element text, otherwise skip.
        check_meta_data : bool, optional
            If True, check that symbol name and description are the same, otherwise skip.
        verbose : bool, optional
            If True, return an exception from the asserter describing the nature of the difference.

        Returns
        -------
        bool
            True if the two symbols are equal in the specified aspects; False if they are not equal and verbose is False.

        Examples
        --------
        >>> m = gt.Container()
        >>> i = gt.Set(m, "i")
        >>> j = gt.Alias(m, "j", i)
        >>> print(i.equals(j))  # Compare the Set 'i' with the Alias 'j'
        True

        """
        return self.alias_with.equals(
            other,
            check_uels=check_uels,
            check_element_text=check_element_text,
            check_meta_data=check_meta_data,
            verbose=verbose,
        )

    def toList(self, include_element_text: bool = False) -> list:
        """
        Convenience method to return symbol records as a python list

        Parameters
        ----------
        include_element_text : bool, optional
            If True, include the element text as tuples (record, element text).
            If False, return a list of records only.

        Returns
        -------
        list
            A list containing the records of the symbol.

        Examples
        --------
        >>> m = gt.Container()
        >>> i = gt.Set(m, "i", records=["new-york", "chicago", "topeka"])
        >>> j = gt.Alias(m, "j", i)
        >>> print(j.toList())
        ['new-york', 'chicago', 'topeka']

        """
        return self.alias_with.toList(include_element_text=include_element_text)

    def pivot(
        self,
        index: Optional[Union[List[str], str]] = None,
        columns: Optional[Union[List[str], str]] = None,
        fill_value: Optional[Union[int, float]] = None,
    ) -> pd.DataFrame:
        """
        Convenience function to pivot records into a new shape (only symbols with > 1D can be pivoted).

        Parameters
        ----------
        index : List[str] | str, optional
            If index is None then it is set to dimensions [0..dimension-1]
        columns : List[str] | str, optional
            If columns is None then it is set to the last dimension.
        fill_value : int | float, optional
            Missing values in the pivot will take the value provided by fill_value

        Returns
        -------
        DataFrame
            A new DataFrame containing the pivoted data.

        Examples
        --------
        >>> m = gt.Container()
        >>> i = gt.Set(m, "i", records=["seattle", "san-diego"])
        >>> j = gt.Set(m, "j", records=["new-york", "chicago", "topeka"])
        >>> ij = gt.Set(m, "ij", [i,j], records=[("seattle", "chicago"), ("seattle", "topeka"), ("san-diego", "new-york")])
        >>> routes = gt.Alias(m, name="routes", alias_with=ij)
        >>> print(routes.pivot(fill_value=""))
                  chicago topeka new-york
        seattle      True   True
        san-diego                    True

        """
        return self.alias_with.pivot(
            index=index, columns=columns, fill_value=fill_value
        )

    def getSparsity(self) -> Union[float, None]:
        """
        Gets the sparsity of the symbol w.r.t the cardinality

        Returns
        -------
        float | None
            Sparsity of an alias
        """
        return self.alias_with.getSparsity()

    @property
    def is_singleton(self) -> bool:
        """
        if symbol is a singleton set

        Returns
        -------
        bool
            True if the alias is singleton; False otherwise
        """
        return self.alias_with.is_singleton

    @is_singleton.setter
    def is_singleton(self, is_singleton: bool) -> None:
        self.alias_with.is_singleton = is_singleton
        self.modified = True

    def getDomainViolations(self) -> Union[List["DomainViolation"], None]:
        """
        Returns a list of DomainViolation objects if any (None otherwise)

        Returns
        -------
        List[DomainViolation] | None
            A list of DomainViolation objects if any (None otherwise)
        """
        return self.alias_with.getDomainViolations()

    def findDomainViolations(self) -> pd.DataFrame:
        """
        Get a view of the records DataFrame that contain any domain violations

        Returns
        -------
        DataFrame
            A DataFrame containing the records that contain any domain violations.
            If there are no violations, an empty DataFrame is returned.
        """
        return self.alias_with.findDomainViolations()

    def hasDomainViolations(self) -> bool:
        """
        Returns True if there are domain violations in the records of the parent set, returns False if not.

        Returns
        -------
        bool
            True if there are domain violations in the records of the parent set; False otherwise
        """
        return self.alias_with.hasDomainViolations()

    def countDomainViolations(self) -> int:
        """
        Returns the count of how many records in the parent set contain at least one domain violation

        Returns
        -------
        int
            The count of how many records in the parent set contain at least one domain violation
        """
        return self.alias_with.countDomainViolations()

    def dropDomainViolations(self) -> None:
        """
        Drop records from the parent set that contain a domain violation
        """
        return self.alias_with.dropDomainViolations()

    def countDuplicateRecords(self) -> int:
        """
        Returns the count of how many (case insensitive) duplicate records exist in the parent set

        Returns
        -------
        int
            The count of how many (case insensitive) duplicate records exist in the parent set
        """
        return self.alias_with.countDuplicateRecords()

    def findDuplicateRecords(self, keep: Union[str, bool] = "first") -> pd.DataFrame:
        """
        Get a view of the records DataFrame that contain any domain violations.

        Parameters
        ----------
        keep : str, optional
            Specifies how to handle duplicates. Options are:
            - 'first' (default): Keeps the first occurrence and removes subsequent duplicates.
            - 'last': Keeps the last occurrence and removes previous duplicates.
            - False: Keeps all duplicates.

        Returns
        -------
        DataFrame
            A DataFrame of the records that contain any domain violations.
            If there are no duplicates, an empty DataFrame is returned.
        """
        return self.alias_with.findDuplicateRecords(keep=keep)

    def hasDuplicateRecords(self) -> bool:
        """
        Returns True if there are (case insensitive) duplicate records in the parent set, returns False if not.

        Returns
        -------
        bool
            True if there are (case insensitive) duplicate records in the parent set; False otherwise
        """
        return self.alias_with.hasDuplicateRecords()

    def dropDuplicateRecords(self, keep: Union[str, bool] = "first") -> None:
        """
        Drop records with (case insensitive) duplicate domains from the parent set

        Parameters
        ----------
        keep : str, optional
            Specifies how to handle duplicates. Options are:
            - 'first' (default): keeps the first instance of a duplicate record
            - 'last': keeps the last instance of a record
            - False: drops all duplicates including the first and last
        """
        return self.alias_with.dropDuplicateRecords(keep=keep)

    def _getUELCodes(self, dimension, ignore_unused=False):
        return self.alias_with._getUELCodes(dimension, ignore_unused=ignore_unused)

    def getUELs(
        self,
        dimensions: Optional[Union[List[int], int]] = None,
        codes: Optional[Union[List[int], int]] = None,
        ignore_unused: bool = False,
    ) -> List[str]:
        """
        Gets UELs from the parent set dimensions. If dimensions is None then get UELs from all dimensions (maintains order).
        The argument codes accepts a list of str UELs and will return the corresponding int; must specify a single dimension if passing codes.

        Parameters
        ----------
        dimensions : List[int] | int, optional
        codes : List[int] | int, optional
        ignore_unused : bool, optional

        Returns
        -------
        List[str]
            Returns only UELs in the data if ignore_unused=True, otherwise return all UELs.
        """
        return self.alias_with.getUELs(
            dimensions=dimensions, codes=codes, ignore_unused=ignore_unused
        )

    def lowerUELs(self, dimensions: Optional[Union[List[int], int]] = None) -> "Alias":
        """
        Lowercase the UELs of an Alias.

        Parameters
        ----------
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with lowercase UELs.
        """
        self.alias_with.lowerUELs(dimensions=dimensions)
        return self

    def upperUELs(self, dimensions: Optional[Union[List[int], int]] = None) -> "Alias":
        """
        Uppercase the UELs of an Alias.

        Parameters
        ----------
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with uppercase UELs.
        """
        self.alias_with.upperUELs(dimensions=dimensions)
        return self

    def lstripUELs(self, dimensions: Optional[Union[List[int], int]] = None) -> "Alias":
        """
        Remove leading whitespaces from the UELs of an Alias.

        Parameters
        ----------
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with processed UELs.
        """
        self.alias_with.lstripUELs(dimensions=dimensions)
        return self

    def rstripUELs(self, dimensions: Optional[Union[List[int], int]] = None) -> "Alias":
        """
        Remove trailing whitespaces from the UELs of an Alias.

        Parameters
        ----------
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with processed UELs.
        """
        self.alias_with.rstripUELs(dimensions=dimensions)
        return self

    def stripUELs(self, dimensions: Optional[Union[List[int], int]] = None) -> "Alias":
        """
        Remove leading and trailing whitespaces from the UELs of an Alias.

        Parameters
        ----------
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with processed UELs.
        """
        self.alias_with.stripUELs(dimensions=dimensions)
        return self

    def capitalizeUELs(
        self, dimensions: Optional[Union[List[int], int]] = None
    ) -> "Alias":
        """
        Capitalizes the first character of UELs of an Alias

        Parameters
        ----------
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with processed UELs.
        """
        self.alias_with.capitalizeUELs(dimensions=dimensions)
        return self

    def casefoldUELs(
        self, dimensions: Optional[Union[List[int], int]] = None
    ) -> "Alias":
        """
        Casefolds the UELs of an Alias

        Parameters
        ----------
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with processed UELs.
        """
        self.alias_with.casefoldUELs(dimensions=dimensions)
        return self

    def titleUELs(self, dimensions: Optional[Union[List[int], int]] = None) -> "Alias":
        """
        Converts the UELs of an Alias to title style; new-york -> New-York

        Parameters
        ----------
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with processed UELs.
        """
        self.alias_with.titleUELs(dimensions=dimensions)
        return self

    def ljustUELs(
        self,
        length: int,
        fill_character: Optional[str] = None,
        dimensions: Optional[Union[List[int], int]] = None,
    ) -> "Alias":
        """
        Left-justifies the UELs of an Alias, padding them with a specified fill character to reach the desired length.

        Parameters
        ----------
        length : int
            The target length to which UELs will be left-justified.

        fill_character : str, optional
            The character used for padding the UELs to the specified length. If not provided, it defaults to a whitespace.

        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with processed UELs.
        """
        self.alias_with.ljustUELs(
            length, fill_character=fill_character, dimensions=dimensions
        )
        return self

    def rjustUELs(
        self,
        length: int,
        fill_character: Optional[str] = None,
        dimensions: Optional[Union[List[int], int]] = None,
    ) -> "Alias":
        """
        Left-justifies the UELs of an Alias, padding them with a specified fill character to reach the desired length.

        Parameters
        ----------
        length : int
            The target length to which UELs will be left-justified.

        fill_character : str, optional
            The character used for padding the UELs to the specified length. If not provided, it defaults to a whitespace.

        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.

        Returns
        -------
        Alias
            The Alias with processed UELs.
        """
        self.alias_with.rjustUELs(
            length, fill_character=fill_character, dimensions=dimensions
        )
        return self

    def setUELs(
        self,
        uels: Union[List[str], str],
        dimensions: Optional[Union[List[int], int]] = None,
        rename: bool = False,
    ) -> None:
        """
        Set the UELs for parent set dimensions. If dimensions is None then set UELs for all dimensions.
        If rename=True, then the old UEL names will be renamed with the new UEL names. ** All trailing whitespace is trimmed **

        Parameters
        ----------
        uels : List[str] | str
            UELs to be set
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.
        rename : bool, optional
            If True, then the old UEL names will be renamed with the new UEL names. By default False
        """
        return self.alias_with.setUELs(uels=uels, dimensions=dimensions, rename=rename)

    def reorderUELs(
        self,
        uels: Optional[Union[List[str], str]] = None,
        dimensions: Optional[Union[List[int], int]] = None,
    ) -> None:
        """
        Reorders the UELs in the parent set dimensions. If uels is None, reorder UELs to data order and append any unused categories.
        If dimensions is None then reorder UELs in all dimensions of the parent set.

        Parameters
        ----------
        uels : List[str] | str, optional
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.
        """
        return self.alias_with.reorderUELs(uels=uels, dimensions=dimensions)

    def addUELs(
        self,
        uels: Union[List[str], str],
        dimensions: Optional[Union[List[int], int]] = None,
    ) -> None:
        """
        Adds UELs to the parent set dimensions. If dimensions is None then add UELs to all dimensions. ** All trailing whitespace is trimmed **

        Parameters
        ----------
        uels : List[str] | str
            UELs to be added
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.
        """
        return self.alias_with.addUELs(uels=uels, dimensions=dimensions)

    def removeUELs(
        self,
        uels: Optional[Union[List[str], str]] = None,
        dimensions: Optional[Union[List[int], int]] = None,
    ) -> None:
        """
        Removes UELs that appear in the parent set dimensions, If uels is None then remove all unused UELs (categories). If dimensions is None then operate on all dimensions.

        Parameters
        ----------
        uels : List[str] | str, optional
            UELs to be removed
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.
        """
        return self.alias_with.removeUELs(uels=uels, dimensions=dimensions)

    def renameUELs(
        self,
        uels: Union[List[str], str],
        dimensions: Optional[Union[List[int], int]] = None,
        allow_merge: bool = False,
    ) -> None:
        """
        Renames UELs (case-sensitive) that appear in the parent set dimensions. If dimensions is None then operate on all dimensions of the symbol.
        If allow_merge=True, the categorical object will be re-created to offer additional data flexibility. ** All trailing whitespace is trimmed **

        Parameters
        ----------
        uels : List[str] | str
            UELs to be renamed
        dimensions : List[int] | int, optional
            Dimensions of the Alias to be processed. You can provide a single dimension as an int
            or a list of dimensions. If not specified, it will process all dimensions.
        allow_merge : bool
            If True, the categorical object will be re-created to offer additional data flexibility
        """
        return self.alias_with.renameUELs(
            uels=uels, dimensions=dimensions, allow_merge=allow_merge
        )

    def _assert_valid_records(self):
        self.alias_with._assert_valid_records()

    def _assert_is_valid(self):
        if self._requires_state_check:
            if self.container is None:
                raise Exception(
                    "Symbol is not currently linked to a container, "
                    "must add it to a container in order to be valid"
                )

            if self.alias_with is None:
                raise Exception(
                    "Alias symbol is not valid because it is not currently linked to a parent set"
                )

            if not self.alias_with.isValid():
                raise Exception(
                    "Alias symbol is not valid because parent "
                    f"set '{self.alias_with.name}' is not valid"
                )
            # if no exceptions, then turn self._requires_state_check 'off'
            self._requires_state_check = False

    @property
    def alias_with(self) -> "Set":
        """
        Returns the aliased object

        Returns
        -------
        Set
            The aliased Set
        """
        return self._alias_with

    @alias_with.setter
    def alias_with(self, alias_with):
        if isinstance(alias_with, ABCUniverseAlias):
            raise TypeError(
                "Cannot create an Alias to a UniverseAlias, create a new UniverseAlias symbol instead."
            )

        if not isinstance(alias_with, (ABCSet, ABCAlias)):
            raise TypeError("Symbol 'alias_with' must be type Set or Alias")

        if isinstance(alias_with, ABCAlias):
            parent = alias_with
            while not isinstance(parent, ABCSet):
                parent = parent.alias_with
            alias_with = parent

        # check to see if _alias_with is being changed
        if getattr(self, "_alias_with", None) != alias_with:
            self._requires_state_check = True
            self._alias_with = alias_with
            self.modified = True

            if isinstance(self.container, ABCContainer):
                self.container._requires_state_check = True
                self.container.modified = True

    @property
    def domain_names(self) -> List[str]:
        """
        Returns the string version of domain names

        Returns
        -------
        List[str]
            A list of string version of domain names
        """
        return self.alias_with.domain_names

    @property
    def domain(self) -> List[Union["Set", str]]:
        """
        Returns list of domains given either as string (* for universe set) or as reference to the Set/Alias object

        Returns
        -------
        List[Set | str]
            A list of domains given either as string (* for universe set) or as reference to the Set/Alias object
        """
        return self.alias_with.domain

    @domain.setter
    def domain(self, domain):
        self.alias_with.domain = domain
        self.modified = True
        self.container.modified = True

    @property
    def domain_type(self) -> Union[str, None]:
        """
        Returns the state of domain links

        Returns
        -------
        str
            none, relaxed or regular
        """
        return self.alias_with.domain_type

    @property
    def description(self) -> str:
        """
        Returns description of symbol

        Returns
        -------
        str
            Description of symbol
        """
        return self.alias_with.description

    @description.setter
    def description(self, description):
        self.alias_with.description = description
        self.modified = True
        self.container.modified = True

    @property
    def dimension(self) -> int:
        """
        Returns the dimension of symbol

        Returns
        -------
        int
            Dimension of symbol
        """
        return self.alias_with.dimension

    @dimension.setter
    def dimension(self, dimension):
        self.alias_with.dimension = dimension
        self.modified = True
        self.container.modified = True

    @property
    def records(self) -> Union[pd.DataFrame, None]:
        """
        Returns the main symbol records

        Returns
        -------
        DataFrame | None
            The main symbol records, None if no records were set
        """
        return self.alias_with.records

    @records.setter
    def records(self, records):
        self.alias_with.records = records
        self.modified = True
        self.container.modified = True

    def setRecords(self, records: Any, uels_on_axes: bool = False) -> None:
        """
        main convenience method to set standard pandas.DataFrame formatted records.
        If uels_on_axes=True setRecords will assume that all domain information is contained in the axes of the pandas object – data will be flattened (if necessary).

        Parameters
        ----------
        records : Any
        uels_on_axes : bool, optional
        """
        self.alias_with.setRecords(records, uels_on_axes=uels_on_axes)

    @property
    def number_records(self) -> int:
        """
        Returns the number of symbol records

        Returns
        -------
        int
            Number of symbol records
        """
        return self.alias_with.number_records

    @property
    def domain_labels(self) -> Union[List[str], None]:
        """
        Returns the column headings for the records DataFrame

        Returns
        -------
        Union[List[str], None]
            Column headings for the records DataFrame
        """
        return self.alias_with.domain_labels

    @domain_labels.setter
    def domain_labels(self, labels):
        self.alias_with.domain_labels = labels

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
            "alias_with": self.alias_with.name,
            "is_singleton": self.is_singleton,
            "domain": self.domain_names,
            "domain_type": self.domain_type,
            "dimension": self.dimension,
            "number_records": self.number_records,
        }
