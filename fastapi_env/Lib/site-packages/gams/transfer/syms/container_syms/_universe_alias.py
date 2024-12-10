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
from gams.transfer._abcs import ABCUniverseAlias, ABCAlias, AnyContainerSymbol
from gams.transfer.syms._mixins import SAUAMixin, SAUAPVEMixin
from typing import Union, List, TYPE_CHECKING

if TYPE_CHECKING:
    from gams.transfer import Container, Set, Alias


class UniverseAlias(SAUAMixin, SAUAPVEMixin, ABCUniverseAlias):
    """
    Universe Alias symbol

    Parameters
    ----------
    container : Container
    name : str

    Examples
    --------
    >>> import gams.transfer as gt
    >>> m = gt.Container()
    >>> i = gt.Set(m, "i", records=["seattle", "san-diego"])
    >>> j = gt.Set(m, "j", records=["new-york", "chicago", "topeka"])
    >>> ij = gt.UniverseAlias(m, "ij")
    >>> print(ij.toList())
    ['seattle', 'san-diego', 'new-york', 'chicago', 'topeka']

    Attributes
    ----------
    alias_with : str
        Aliased object
    container : Container object
        Container where the symbol exists
    description : str
        description of symbol
    dimension : int
        The dimension of symbol
    domain : List[str]
        List of domains given as string (* for universe set)
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
    def _from_gams(cls, container, name):
        # create new symbol object
        obj = UniverseAlias.__new__(cls)

        # set private properties directly
        obj._requires_state_check = False
        obj._container = weakref.proxy(container)
        obj._name = name
        obj._modified = True

        # typing
        obj._gams_type = gdx.GMS_DT_ALIAS
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

    def __init__(self, container: "Container", name: str) -> None:
        self._requires_state_check = True
        self.container = container
        self.name = name
        self.modified = True
        self._gams_type = gdx.GMS_DT_ALIAS
        self._gams_subtype = 0
        container.data.update({name: self})

    def __delitem__(self):
        # TODO: add in some functionality that might relax the symbols down to a different domain
        #       This function would mimic the <Container>.removeSymbols() method -- is more pythonic
        del self.container.data[self.name]

    def __repr__(self):
        return f"<UniverseAlias `{self.name}` ({hex(id(self))})>"

    @property
    def is_singleton(self) -> bool:
        """
        Whether a symbol is a singleton set

        Returns
        -------
        bool
            Always False
        """
        return False

    def _assert_is_valid(self):
        if self._requires_state_check:
            if self.container is None:
                raise Exception(
                    "Symbol is not currently linked to a container, "
                    "must add it to a container in order to be valid"
                )

            # if no exceptions, then turn self._requires_state_check 'off'
            self._requires_state_check = False

    @property
    def alias_with(self) -> str:
        """
        Returns aliased object

        Returns
        -------
        str
            Always "*"
        """
        return "*"

    @property
    def domain_names(self) -> List[str]:
        """
        Always ["*"] for universe alias

        Returns
        -------
        List[str]
            Always ["*"]
        """
        return ["*"]

    @property
    def domain_labels(self) -> List[str]:
        """
        Always ["uni"] for universe alias

        Returns
        -------
        List[str]
            Always ["uni"]
        """
        return ["uni"]

    @property
    def domain(self) -> List[str]:
        """
        Always ["*"] for universe alias

        Returns
        -------
        List[str]
            Always ["*"]
        """
        return ["*"]

    @property
    def description(self) -> str:
        """
        Always 'Aliased with *' for universe alias

        Returns
        -------
        str
            Always 'Aliased with *'
        """
        return "Aliased with *"

    @property
    def dimension(self) -> int:
        """
        Always 1 for universe alias

        Returns
        -------
        int
            Always 1
        """
        return 1

    def toList(self) -> Union[List[str], None]:
        """
        Convenience method to return symbol records as a python list

        Returns
        -------
        List[str] | None
            A list of symbol records

        Examples
        --------
        >>> m = gt.Container()
        >>> i = gt.Set(m, "i", records=["seattle", "san-diego"])
        >>> j = gt.Set(m, "j", records=["new-york", "chicago", "topeka"])
        >>> ij = gt.UniverseAlias(m, "ij")
        >>> print(ij.toList())
        ['seattle', 'san-diego', 'new-york', 'chicago', 'topeka']
        """
        if self.records is not None:
            return self.records.set_index(self.records.columns[0]).index.to_list()
        return None

    @property
    def records(self) -> Union[pd.DataFrame, None]:
        """
        The main symbol records

        Returns
        -------
        DataFrame | None
            Records dataframe if there are records, otherwise None.
        """
        if self.isValid():
            return pd.DataFrame(
                data=self.container.getUELs(), columns=self.domain_labels
            )
        return None

    @property
    def number_records(self) -> Union[int]:
        """
        Number of symbol records (i.e., returns len(records) if not NAN)

        Returns
        -------
        int
            Number of symbol records
        """
        if self.isValid():
            return len(self.records)

        return float("nan")

    @property
    def domain_type(self) -> str:
        """
        Always none for universe alias

        Returns
        -------
        str
            Always 'none'
        """
        return "none"

    def getUELs(self, ignore_unused: bool = False) -> Union[List[str], None]:
        """
        Gets UELs from the Container. Returns only UELs in the data if ignore_unused=True, otherwise return all UELs.

        Parameters
        ----------
        ignore_unused : bool, optional
            Whether to get all UELs or only used ones, by default False

        Returns
        -------
        list | None
            A list of UELs if the symbol is valid, otherwise None.
        """
        if self.isValid():
            return self.container.getUELs(ignore_unused=ignore_unused)
        return None

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
            "alias_with": self.alias_with,
        }

    def equals(
        self,
        other: Union["Set", "Alias"],
        check_meta_data: bool = True,
        verbose: bool = False,
    ):
        """
        Used to compare the symbol to another symbol.
        If check_meta_data=True then check that symbol name and description are the same, otherwise skip.
        If verbose=True will return an exception from the asserter describing the nature of the difference.

        Parameters
        ----------
        other : Set or Alias
            The other symbol (Set or Alias) to compare with the current alias.
        check_meta_data : bool, optional
            If True, compare the metadata of the two symbols, by default True.
        verbose : bool, optional
            If True, raise an exception with an explanation of where the symbols differ if they do differ, by default False.

        Returns
        -------
        bool
            True if the two symbols are equal in the specified aspects; False if they are not equal and verbose is False.

        Examples
        --------
        >>> m = gt.Container()
        >>> i = gt.Set(m, "i", records=["seattle", "san-diego"])
        >>> j = gt.Set(m, "j", records=["new-york", "chicago", "topeka"])
        >>> ij = gt.UniverseAlias(m, "ij")
        >>> print(ij.equals(i))
        False
        """
        try:
            #
            # ARG: other
            if not isinstance(other, AnyContainerSymbol):
                raise TypeError("Argument 'other' must be a symbol object")

            # adjustments
            if isinstance(other, ABCAlias):
                other = other.alias_with

            #
            # ARG: self & other
            if not isinstance(self, type(other)):
                raise TypeError(
                    f"Symbol are not of the same type (`{type(self)}` != `{type(other)}`)"
                )

            #
            # ARG: check_meta_data
            if not isinstance(check_meta_data, bool):
                raise TypeError("Argument 'check_meta_data' must be type bool")

            #
            # Mandatory checks
            if not self.isValid():
                raise Exception(
                    f"Cannot compare objects because `{self.name}` is not a valid symbol object"
                    "Use `<symbol>.isValid(verbose=True)` to debug further."
                )

            if not other.isValid():
                raise Exception(
                    f"Cannot compare objects because `{other.name}` is not a valid symbol object"
                    "Use `<symbol>.isValid(verbose=True)` to debug further."
                )

            #
            # Check metadata (optional)
            if check_meta_data:
                if self.name != other.name:
                    raise Exception(
                        f"Symbol names do not match (`{self.name}` != `{other.name}`)"
                    )

            if self.getUELs() != other.getUELs():
                raise Exception(
                    "Symbol UEL ordering does not match \n\n"
                    f"[self]: {left_uels} \n"
                    f"[other]: {right_uels} \n"
                )

            return True
        except Exception as err:
            if verbose:
                raise err
            else:
                return False

    def pivot(self, *args, **kwargs) -> None:
        """
        Pivot the records DataFrame of a symbol that has a dimension more than 1.
        Always raises a dimensionality exception.
        """
        raise Exception(
            "Pivoting operations only possible on symbols with dimension > 1, "
            f"symbol dimension is {self.dimension}"
        )

    def getSparsity(self) -> float:
        """
        Get the sparsity of the symbol w.r.t the cardinality

        Returns
        -------
        float
            Always 0
        """
        return 0.0
