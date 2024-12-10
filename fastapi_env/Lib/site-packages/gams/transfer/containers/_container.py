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

import os
import pathlib
import pandas as pd
import numpy as np
import gams.core.numpy as gnp
from gams import GamsWorkspace, GamsDatabase
from gams.core import gmd
from gams.transfer._internals import (
    CasePreservingDict,
    DestinationType,
    check_all_same,
)
import gams.transfer._abcs as abcs
from gams.transfer.containers._mixins import CCCMixin
import gams.transfer.containers._io as io
from gams.transfer.syms import (
    Set,
    Parameter,
    Variable,
    Equation,
    Alias,
    UniverseAlias,
)
from typing import Optional, Union, List, Dict, Any


def get_system_directory(system_directory: Union[None, str]) -> str:
    """
    Gets the GAMS system directory.

    Parameters
    ----------
    system_directory : None | str
        GAMS system directory. If None, itnwill try to get the default one.

    Returns
    -------
    str
        GAMS system directory.

    Raises
    ------
    Exception
        If no default system directory for a GAMS installation is found.
    """
    if system_directory is None:
        try:
            ws = GamsWorkspace()
            sysdir = pathlib.Path(ws.system_directory)
        except:
            raise Exception(
                "Could not find a GAMS installation, "
                "must manually specify system_directory"
            )
    else:
        sysdir = pathlib.Path(system_directory)

    return os.fspath(sysdir.expanduser().resolve())


class Container(CCCMixin, abcs.ABCContainer):
    """
    A container is an object that holds all symbols and operates on them.

    Parameters
    ----------
    load_from : GamsDatabase | PathLike | str | ABCContainer, optional
        The data source to read from, by default None
    system_directory : str, optional
        Path to the directory that holds the GAMS installation, by default None

    Examples
    --------
    >>> import gams.transfer as gt
    >>> m = gt.Container()
    >>> i = gt.Set(m, "i")

    Attributes
    ----------
    data : dict
        Dictionary that lists symbol names and symbol objects
    modified : bool
        Flag that identifies if the container has been modified
    summary : dict
        Returns a dict of only the metadata
    system_directory : str
        Returns the path to the system directory
    """

    def __init__(
        self,
        load_from: Optional[
            Union["GamsDatabase", os.PathLike, str, "abcs.ABCContainer"]
        ] = None,
        system_directory: Optional[str] = None,
    ) -> None:
        # set up
        self.system_directory = get_system_directory(system_directory)
        self._gams2np = gnp.Gams2Numpy(self.system_directory)
        self.data = CasePreservingDict()
        self.modified = True
        self._requires_state_check = True

        # read
        if load_from is not None:
            self.read(load_from)

    def __iter__(self):
        return iter(self.data.items())

    def __repr__(self):
        return f"<GAMS Transfer Container ({hex(id(self))})>"

    def __str__(self):
        if len(self):
            return f"<GAMS Transfer Container (w/ {len(self)} symbols)>"
        else:
            return f"<GAMS Transfer Container (empty)>"

    def __getitem__(self, sym):
        try:
            return self.data[sym]
        except KeyError:
            raise KeyError(
                f"Attempted retrieval of symbol `{sym}`, but `{sym}` does not"
                " exist in the Container"
            )

    def __contains__(self, sym) -> bool:
        if isinstance(sym, abcs.AnyContainerSymbol):
            return hex(id(sym)) in [hex(id(i)) for i in self.data.values()]
        elif isinstance(sym, str):
            return sym in self.data
        else:
            return False

    @property
    def system_directory(self):
        """
        This property returns the path to the GAMS system directory.

        Returns
        -------
        str
            The path to the system directory.
        """
        return self._system_directory

    @system_directory.setter
    def system_directory(self, sysdir: Union[os.PathLike, str]) -> None:
        """
        Path to the system directory.

        Parameters
        ----------
        sysdir : PathLike | str
            The path to the system directory.
        """
        if not isinstance(sysdir, (os.PathLike, str)):
            raise TypeError(
                "'system_directory' expects type str or PathLike object, got"
                f" {type(sysdir)}"
            )

        sysdir = pathlib.Path(sysdir).expanduser().resolve()

        if not sysdir.is_dir():
            raise Exception(
                f"GAMS system_directory '{os.fspath(sysdir)}' is not a" " directory"
            )

        if not sysdir.exists():
            raise Exception(
                f"GAMS system_directory '{os.fspath(sysdir)}' does not exist, "
                "check spelling or path specification"
            )

        if not pathlib.Path(sysdir, "optgams.def").is_file():
            raise Exception(
                f"GAMS system_directory '{os.fspath(sysdir)}' is not a valid"
                " GAMS directory"
            )

        self._system_directory = os.fspath(sysdir)

    @property
    def summary(self) -> dict:
        """
        This property returns a summary of the container.

        Returns
        -------
        dict
            A summary including the container's system directory and its number of symbols.
        """
        return {
            "system_directory": self.system_directory,
            "number_symbols": len(self),
        }

    def _check_format_uels(self, symbols):
        if not isinstance(symbols, (str, list, type(None))):
            raise Exception("Argument 'symbols' must be type str, list or NoneType.")

        if symbols is None:
            symbols = self.listSymbols(is_valid=True)

        if isinstance(symbols, str):
            symbols = [symbols]

        if any(not isinstance(i, str) for i in symbols):
            raise Exception("Argument 'symbols' must only contain type str")

        return symbols

    def _formatUELs(self, method, symbols=None):
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            do_format = getattr(symobj, method)
            do_format()

    def lowerUELs(self, symbols: Optional[Union[str, List[str]]] = None) -> "Container":
        """
        This function converts the UELs of specific symbols to lowercase. If the 'symbols' parameter is set to None (default), all symbols in the container will be processed.

        Parameters
        ----------
        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you want to convert to lowercase. By default, it is set to None.

        Returns
        -------
        Container
            The updated container with some UELs converted to lowercase.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            symobj.lowerUELs()

        return self

    def upperUELs(self, symbols: Optional[Union[str, List[str]]] = None) -> "Container":
        """
        This function converts the UELs of specific symbols to uppercase. If the 'symbols' parameter is set to None (default), all symbols in the container will be processed.

        Parameters
        ----------
        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you want to convert to uppercase. By default, it is set to None.

        Returns
        -------
        Container
            The updated container with some UELs converted to uppercase.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            symobj.upperUELs()

        return self

    def lstripUELs(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> "Container":
        """
        This function removes leading whitespaces from the UELs of specific symbols. If the 'symbols' parameter is set to None (default), all symbols in the container will undergo this operation.

        Parameters
        ----------
        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you wish to process. By default, it is set to None.

        Returns
        -------
        Container
            The updated container with leading whitespaces removed from the UELs of some symbols.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            symobj.lstripUELs()

        return self

    def rstripUELs(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> "Container":
        """
        This function removes trailing whitespaces from the UELs of specific symbols. If the 'symbols' parameter is set to None (default), all symbols in the container will undergo this operation.

        Parameters
        ----------
        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you wish to process. By default, it is set to None.

        Returns
        -------
        Container
            The updated container with trailing whitespaces removed from the UELs of some symbols.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            symobj.rstripUELs()

        return self

    def stripUELs(self, symbols: Optional[Union[str, List[str]]] = None) -> "Container":
        """
        This function removes leading and trailing whitespaces from the UELs of specific symbols. If the 'symbols' parameter is set to None (default), all symbols in the container will undergo this operation.

        Parameters
        ----------
        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you wish to process. By default, it is set to None.

        Returns
        -------
        Container
            The updated container with leading and trailing whitespaces removed from the UELs of some symbols.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            symobj.stripUELs()

        return self

    def capitalizeUELs(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> "Container":
        """
        This function capitalizes the UELs of specific symbols. If the 'symbols' parameter is set to None (default), all symbols in the container will undergo this capitalization operation.

        Parameters
        ----------
        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you wish to capitalize. By default, it is set to None.

        Returns
        -------
        Container
            The updated container with UELs capitalized for some symbols.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            symobj.capitalizeUELs()

        return self

    def casefoldUELs(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> "Container":
        """
        This function performs case folding on the UELs of specific symbols, converting them to lowercase. If the 'symbols' parameter is set to None (default), all symbols in the container will undergo this case folding operation.

        Parameters
        ----------
        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you wish to convert to lowercase. By default, it is set to None.

        Returns
        -------
        Container
            The updated container with UELs converted to lowercase for some symbols.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            symobj.casefoldUELs()

        return self

    def titleUELs(self, symbols: Optional[Union[str, List[str]]] = None) -> "Container":
        """
        This function capitalizes the UELs of specific symbols in title case. If the 'symbols' parameter is set to None (default), all symbols in the container will undergo this capitalization operation.

        Parameters
        ----------
        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you wish to capitalize in title case. By default, it is set to None.

        Returns
        -------
        Container
            The updated container with UELs capitalized in title case for some symbols.

        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            symobj.titleUELs()

        return self

    def ljustUELs(
        self,
        length: int,
        fill_character: Optional[str] = None,
        symbols: Optional[Union[str, List[str]]] = None,
    ) -> "Container":
        """
        This function left-justifies the UELs of specific symbols within the container, padding them with a specified fill character to reach the desired length.

        Parameters
        ----------
        length : int
            The target length to which UELs will be left-justified.

        fill_character : str, optional
            The character used for padding the UELs to the specified length. If not provided, it defaults to a whitespace.

        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you want to left-justify. By default, it is set to None, meaning all symbols in the container will undergo this left-justification.

        Returns
        -------
        Container
            The updated container with UELs left-justified for some symbols.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            try:
                symobj.ljustUELs(length, fill_character)
            except Exception as err:
                raise Exception(
                    "Could not successfully left justify (ljust) categories"
                    f" in `{symobj.name}`. Reason: {err}"
                )

        return self

    def rjustUELs(
        self,
        length: int,
        fill_character: Optional[str] = None,
        symbols: Optional[Union[str, List[str]]] = None,
    ) -> "Container":
        """
        This function right-justifies the UELs of specific symbols within the container, padding them with a specified fill character to reach the desired length.

        Parameters
        ----------
        length : int
            The target length to which UELs will be right-justified.

        fill_character : str, optional
            The character used for padding the UELs to the specified length. If not provided, it defaults to a whitespace.

        symbols : str | List[str], optional
            The symbol or list of symbols whose UELs you want to right-justify. By default, it is set to None, meaning all symbols in the container will undergo this right-justification.

        Returns
        -------
        Container
            The updated container with UELs right-justified for some symbols.
        """
        symbols = self._check_format_uels(symbols)

        # loop through symbol objects
        for symobj in self.getSymbols(symbols):
            try:
                symobj.rjustUELs(length, fill_character)
            except Exception as err:
                raise Exception(
                    "Could not successfully right justify (rjust) categories"
                    f" in `{symobj.name}`. Reason: {err}"
                )
        return self

    def getUELs(
        self,
        symbols: Optional[Union[str, List[str]]] = None,
        ignore_unused: bool = False,
        unique_only: bool = False,
    ) -> List[str]:
        """
        Retrieve the (UELs) associated with one or more symbols in the Container.

        This method retrieves the (UELs) corresponding to the specified symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the symbol names for which to retrieve UELs, by default None.

        ignore_unused : bool, optional
            A flag to whether or not include unused symbols, by default False

        unique_only : bool, optional
            A flag to whether or not return only unique UELs, by default False

        Returns
        -------
        List[str]
            A list of (UELs) associated with the specified symbols.

        Raises
        ------
        TypeError
            If 'unique_only' is not of type bool.
        TypeError
            If 'symbols' is not of type str, iterable, or NoneType.
        TypeError
            If 'ignore_unused' is not of type bool.
        Exception
            If an element in 'symbols' is not of type str.
        """

        if not isinstance(unique_only, bool):
            raise Exception("Argument 'unique_only' must be type bool.")

        if not isinstance(symbols, (str, list, type(None))):
            raise Exception("Argument 'symbols' must be type str, list or NoneType.")

        if symbols is None:
            symbols = self.listSymbols(is_valid=True)

        if isinstance(symbols, str):
            symbols = [symbols]

        if not isinstance(ignore_unused, bool):
            raise TypeError(f"Argument 'ignore_unused' must be type bool")

        if any(not isinstance(i, str) for i in symbols):
            raise Exception("Argument 'symbols' must only contain type str")

        # loop through symbol objects and get UELs
        uni = {}
        for symobj in self.getSymbols(symbols):
            if not isinstance(symobj, abcs.AnyContainerAlias):
                if symobj.records is not None:
                    uni.update(
                        dict.fromkeys(symobj.getUELs(ignore_unused=ignore_unused))
                    )

        if unique_only:
            return list(CasePreservingDict().fromkeys(uni.keys()).keys())
        else:
            return list(uni.keys())

    def renameUELs(
        self,
        uels: Dict[str, str],
        symbols: Optional[List[str]] = None,
        allow_merge: bool = False,
    ) -> None:
        """
        Rename unique element labels (UELs) associated with symbols in the Container.

        Parameters
        ----------
        uels : Dict[str, str]
            A dictionary mapping old UELs to their new names. The keys are the old UELs that you want to rename,
            and the values are the new names for those UELs

        symbols : List[str]], optional
            An optional parameter specifying the symbol names for which you want to rename UELs, by default None

        allow_merge : bool, optional
            A flag that allows merging UELs with existing UELs, by default False

        Raises
        ------
        Exception
            If the Container is currently invalid (not valid) because UELs (categories) cannot be accessed.
        TypeError
            If 'uels' is not of type dict.
        TypeError
            If 'symbols' is not of type list or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.
        """
        if not self.isValid():
            raise Exception(
                "Container is currently invalid -- must be valid in order to"
                " access UELs (categories)."
            )

        # ARG: uels
        if not isinstance(uels, dict):
            raise TypeError("Argument 'uels' must be type dict")

        # ARG: symbols
        if not isinstance(symbols, (list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            symbols = list(self.data.keys())

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        for symobj in self.getSymbols(symbols):
            if not isinstance(symobj, abcs.ABCUniverseAlias):
                symobj.renameUELs(uels, allow_merge=allow_merge)

    def removeUELs(
        self,
        uels: Optional[Union[str, List[str]]] = None,
        symbols: Optional[List[str]] = None,
    ) -> None:
        """
        Remove specific unique element labels (UELs) from one or more symbols in the Container.

        Parameters
        ----------
        uels : str | List[str], optional
            An optional parameter specifying the unique element labels (UELs) to be removed from the symbols, by default None

        symbols : List[str], optional
            An optional parameter specifying the symbols from which to remove the specified UELs, by default None

        Raises
        ------
        TypeError
            If 'uels' is not of type list, str, or NoneType.
        TypeError
            If an element in 'uels' is not of type str.
        TypeError
            If 'symbols' is not of type list or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.

        Exception
            If the Container is currently invalid, as it must be valid to access UELs (categories).
        """
        if not self.isValid():
            raise Exception(
                "Container is currently invalid -- must be valid in order to"
                " access UELs (categories)."
            )

        if not isinstance(uels, (list, str, type(None))):
            raise TypeError("Argument 'uels' must be type list, str or NoneType")

        if isinstance(uels, str):
            uels = [uels]

        if isinstance(uels, list):
            if any(not isinstance(i, str) for i in uels):
                raise TypeError("Argument 'uels' must contain only type str")

        if not isinstance(symbols, (list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            symbols = list(self.data.keys())

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        for symobj in self.getSymbols(symbols):
            if not isinstance(symobj, abcs.ABCUniverseAlias):
                symobj.removeUELs(uels)

    def getDomainViolations(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> Union[list, None]:
        """
        Get domain violations for one or more symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the symbols for which to retrieve domain violations, by default None

        Returns
        -------
        list | None
            A list of domain violations for the specified symbols, or None if there are no domain violations.

        Raises
        ------
        TypeError
            If 'symbols' is not of type list, str, or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            symbols = list(self.data.keys())

        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        dvs = []
        for symobj in self.getSymbols(symbols):
            violations = symobj.getDomainViolations()
            if violations is not None:
                dvs.extend(violations)

        if len(dvs) != 0:
            return dvs
        else:
            return None

    def hasDomainViolations(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> bool:
        """
        Check if domain violations exist for one or more symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the symbols to check for domain violations, by default None

        Returns
        -------
        bool
            True if domain violations exist for any of the specified symbols, False otherwise.

        Raises
        ------
        TypeError
            If 'symbols' is not of type list, str, or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            symbols = list(self.data.keys())

        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        for symobj in self.getSymbols(symbols):
            if symobj.hasDomainViolations():
                return True

        return False

    def countDomainViolations(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, int]:
        """
        Count domain violations for one or more symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the symbols to count domain violations for, by default None

        Returns
        -------
        Dict[str, int]
            A dictionary where keys are symbol names with domain violations, and values are the corresponding counts of domain violations.

        Raises
        ------
        TypeError
            If 'symbols' is not of type list, str, or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            symbols = list(self.data.keys())

        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        dvs = {}

        for symobj in self.getSymbols(symbols):
            count = symobj.countDomainViolations()
            if count != 0:
                dvs.update({symobj.name: count})

        return dvs

    def dropDomainViolations(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> None:
        """
        Drop domain violations for one or more symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the symbols to drop domain violations for, by default None

        Raises
        ------
        TypeError
            If 'symbols' is not of type list, str, or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type str, list or NoneType")

        if symbols is None:
            symbols = list(self.countDomainViolations().keys())

        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        for symobj in self.getSymbols(symbols):
            symobj.records.drop(index=symobj.findDomainViolations().index, inplace=True)

    def countDuplicateRecords(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, int]:
        """
        Count duplicate records for one or more symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the symbols to count duplicate records for, by default None

        Returns
        -------
        Dict[str, int]
            A dictionary where keys are symbol names with duplicate records, and values are the count of duplicate records for each symbol.

        Raises
        ------
        TypeError
            If 'symbols' is not of type list, str, or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            symbols = list(self.data.keys())

        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        dups = {}

        for symobj in self.getSymbols(symbols):
            count = symobj.countDuplicateRecords()
            if count != 0:
                dups.update({symobj.name: count})

        return dups

    def hasDuplicateRecords(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> bool:
        """
        Check if the Container has any duplicate records for one or more symbols.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the symbols to check for duplicate records, by default None

        Returns
        -------
        bool
            True if duplicate records are found for any of the specified symbols; False otherwise.

        Raises
        ------
        TypeError
            If 'symbols' is not of type list, str, or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            symbols = list(self.data.keys())

        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        for symobj in self.getSymbols(symbols):
            if symobj.hasDuplicateRecords():
                return True

        return False

    def dropDuplicateRecords(
        self,
        symbols: Optional[Union[str, List[str]]] = None,
        keep: str = "first",
    ) -> None:
        """
        Remove duplicate records from the specified symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the symbols from which to remove duplicate records, by default None

        keep : str, optional
            A string indicating which duplicate records to keep, by default "first"

        Raises
        ------
        TypeError
            If 'symbols' is not of type list, str, or NoneType.
        TypeError
            If an element in 'symbols' is not of type str.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            symbols = list(self.countDuplicateRecords().keys())

        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        for symobj in self.getSymbols(symbols):
            symobj.records.drop(
                index=symobj.findDuplicateRecords(keep).index, inplace=True
            )

    def _assert_valid_records(self, symbols=None):
        if symbols is None:
            symbols = self.listSymbols()

        for symobj in self.getSymbols(symbols):
            if not isinstance(symobj, abcs.ABCUniverseAlias):
                symobj._assert_valid_records()

    def _assert_is_valid(self, symbols):
        if self._requires_state_check:
            # make sure that all symbols have consistent naming
            for symname, symobj in zip(symbols, self.getSymbols(symbols)):
                if symname.casefold() != symobj.name.casefold():
                    raise Exception(
                        "Container data dict key is inconsistent with the"
                        f" symbol object name (`{symname}` !="
                        f" `{symobj.name}`). This inconsistency could have"
                        " resulted from a symbol copy/deepcopy operation"
                        " (i.e., `m[<new_symbol>] ="
                        " copy.deepcopy(m[<existing_symbol>])`). Update"
                        " symbol name with `<new_symbol>.name`."
                    )

            # make sure that all symbols reference the correct Container instance
            for symobj in self.getSymbols(symbols):
                if self != symobj.container:
                    raise Exception(
                        f"Symbol `{symobj.name}` has a broken Container"
                        " reference. Symbol references Container at"
                        f" {hex(id(symobj.container))} -- should be"
                        f" referencing Container at {hex(id(self))}. This"
                        " inconsistency could have resulted from a `deepcopy`"
                        " of a symbol object (i.e., `new_container[<symbol>]"
                        " = copy.deepcopy(old_container[<symbol>])`). Update"
                        " symbol reference with `<symbol>.container ="
                        " <new_container>`."
                    )

            if any(not symobj.isValid() for symobj in self.getSymbols(symbols)):
                raise Exception(
                    "Container contains invalid symbols; invalid symbols can"
                    " be found with the"
                    " `<container>.listSymbols(is_valid=False)` method. Debug"
                    " invalid symbol(s) by running"
                    " `<symbol>.isValid(verbose=True, force=True)`` method on"
                    " the symbol object."
                )

            # check if there are graph cycles in the sets
            try:
                self._validSymbolOrder()
            except Exception as err:
                raise err

            # if no exceptions, then turn self._requires_state_check 'off'
            self._requires_state_check = False

    @property
    def modified(self) -> Union[bool, None]:
        return self._modified

    @modified.setter
    def modified(self, modified: bool) -> None:
        if not isinstance(modified, bool):
            raise TypeError("Attribute 'modified' must be type bool")

        self._modified = modified

        if modified is False:
            for symname, symobj in self:
                symobj.modified = False

    def _validSymbolOrder(self):
        ordered_symbols = []
        symbols_to_sort = [k for k, _ in self]

        idx = 0
        while symbols_to_sort:
            sym = symbols_to_sort[idx]

            # special 1D sets (universe domain & relaxed sets)
            if (
                isinstance(self.data[sym], abcs.ABCSet)
                and self.data[sym].dimension == 1
                and isinstance(self.data[sym].domain[0], str)
            ):
                ordered_symbols.append(self.data[sym].name)
                symbols_to_sort.pop(symbols_to_sort.index(sym))
                idx = 0

            # everything else
            else:
                doi = []
                for i in self.data[sym].domain:
                    if isinstance(i, str):
                        doi.append(True)
                    elif (
                        isinstance(i, abcs.AnyContainerDomainSymbol)
                        and i.name in ordered_symbols
                    ):
                        doi.append(True)
                    else:
                        doi.append(False)

                if all(doi):
                    ordered_symbols.append(sym)
                    symbols_to_sort.pop(symbols_to_sort.index(sym))
                    idx = 0
                else:
                    idx += 1

            if idx == len(symbols_to_sort) and symbols_to_sort != []:
                raise Exception(
                    "Graph cycle detected among symbols:"
                    f" {[i for i in symbols_to_sort if isinstance(self.data[i], abcs.ABCSet)]} --"
                    " must resolve circular domain referencing"
                )

        return ordered_symbols

    def reorderSymbols(self) -> None:
        """
        Reorder symbols in order to avoid domain violations
        """
        self.data = CasePreservingDict(
            {k: self.data[k] for k in self._validSymbolOrder()}
        )

    def _isValidSymbolOrder(self):
        valid_order = self._validSymbolOrder()
        current_order = [k for k, _ in self]

        h = []
        for i in current_order:
            if isinstance(self.data[i], abcs.AnyContainerDomainSymbol):
                if current_order.index(i) <= valid_order.index(i):
                    h.append(True)
                else:
                    h.append(False)
            else:
                h.append(True)

        if all(h):
            return True
        else:
            return False

    def hasSymbols(self, symbols: Union[List[str], str]) -> Union[List[bool], bool]:
        """
        Checks if specific symbol names exist in a Container

        Parameters
        ----------
        symbols : List[str] | str
            Symbols to check from the Container

        Returns
        -------
        List[bool] | bool
            Flag to indicate whether a symbol exists or not
        """
        if not isinstance(symbols, (str, list)):
            raise TypeError("Argument 'symbols' must be type str or list")

        if isinstance(symbols, list):
            return [sym in self for sym in symbols]

        if isinstance(symbols, str):
            return symbols in self

    def renameSymbol(self, old_name: str, new_name: str) -> None:
        """
        Rename a symbol in the Container

        Parameters
        ----------
        old_name : str
            Old name of the symbol
        new_name : str
            New name of the symbol
        """
        if not isinstance(old_name, str):
            raise Exception("Argument 'old_name' must be type str")

        if not isinstance(new_name, str):
            raise Exception("Argument 'new_name' must be type str")

        if old_name.casefold() not in self:
            raise KeyError(f"Symbol `{old_name}` does not exist")

        if old_name != new_name:
            self.data[old_name].name = new_name
            self._requires_state_check = True

    def removeSymbols(self, symbols: Optional[Union[List[str], str]] = None) -> None:
        """
        Remove symbols from the Container. If symbols=None, it will remove all symbols.

        Parameters
        ----------
        symbols : List[str] | str, optional
            Symbols to remove from the Container, also sets the symbols container to None. If symbols=None, will remove all symbols.
        """
        if symbols is None:
            self.data = CasePreservingDict()
            return

        # ARG: symbols
        if not isinstance(symbols, (str, list)):
            raise Exception("Argument 'symbols' must be type str or list")

        if isinstance(symbols, str):
            symbols = [symbols]

        if not all([isinstance(i, str) for i in symbols]):
            raise Exception("Argument 'symbols' must contain only type str")

        # test if all symbols are in the Container
        for i in symbols:
            if i not in self:
                raise ValueError(
                    f"User specified to remove symbol `{i}`, "
                    "but it does not exist in the container."
                )

        # find sets or aliases that are being removed
        set_or_alias = []
        [
            set_or_alias.append(symobj)
            for symobj in self.getSymbols(symbols)
            if isinstance(symobj, abcs.AnyContainerDomainSymbol)
        ]

        # remove symbols
        for symobj in self.getSymbols(symbols):
            # mark symbol container as None and reset state check flag
            symobj._container = None
            symobj._requires_state_check = True

            # remove the symbol
            self.data.pop(symobj.name)

        # remove alias symbols if parent is removed
        symbols = list(self)
        for symname, symobj in symbols:
            if isinstance(symobj, abcs.ABCAlias):
                if symobj.alias_with in set_or_alias:
                    self.removeSymbols(symobj.name)

        # search through all symbols and remove domain references
        for symname, symobj in self:
            # find new domain
            new_domain = []
            for n, symdom in enumerate(symobj.domain):
                if symdom in set_or_alias:
                    new_domain.append("*")
                else:
                    new_domain.append(symdom)

            # set new (relaxed) domain
            symobj.domain = new_domain

        # reset flags
        if set_or_alias:
            for symname, symobj in self:
                symobj._requires_state_check = True
                symobj.modified = True

        # reset state check flag for the container
        self._requires_state_check = True

    def addSet(
        self,
        name: str,
        domain: Optional[List[Union["Set", str]]] = None,
        is_singleton: bool = False,
        records: Optional[Any] = None,
        domain_forwarding: bool = False,
        description: str = "",
        uels_on_axes: bool = False,
    ) -> "Set":
        """
        Add a Set symbol to the Container or update an existing Set symbol.

        Parameters
        ----------
        name : str
            The name of the Set symbol to be added or updated.

        domain : List[Set | str], optional
            An optional parameter specifying the domain (index set) of the Set symbol, by default None

        is_singleton : bool, optional
            A boolean indicating whether the Set is a singleton set, by default False

        records : Any, optional
            An optional parameter specifying the records (elements) of the Set symbol.

        domain_forwarding : bool, optional
            A boolean indicating whether domain forwarding is enabled for the Set symbol, by default False

        description : str, optional
            A description or comment for the Set symbol.

        uels_on_axes : bool, optional
            A boolean indicating whether unique element lists (UELs) are used as axis values in the symbol, by default False

        Returns
        -------
        Set
            The Set object that was added or updated in the Container.

        Raises
        ------
        ValueError
            If an attempt is made to update an existing Set symbol with conflicting properties.
        TypeError
            If 'domain' is not of type list, Set, or str.
        TypeError
            If 'is_singleton' is not of type bool.
        TypeError
            If 'domain_forwarding' is not of type bool.
        TypeError
            If 'uels_on_axes' is not of type bool.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = m.addSet("i", records=['i1','i2'])
        >>> print(i.getUELs())
        ['i1', 'i2']

        """
        # allows overwriting
        return Set(
            self,
            name,
            domain,
            is_singleton,
            records,
            domain_forwarding,
            description,
            uels_on_axes,
        )

    def addParameter(
        self,
        name: str,
        domain: Optional[List[Union[str, "Set"]]] = None,
        records: Optional[Any] = None,
        domain_forwarding: bool = False,
        description: str = "",
        uels_on_axes: bool = False,
    ) -> "Parameter":
        """
        Add a Parameter symbol to the Container or update an existing Parameter symbol.

        Parameters
        ----------
        name : str
            The name of the Parameter symbol to be added or updated.

        domain : List[Set | str], optional
            An optional parameter specifying the domain (index set) of the Parameter symbol, by default None

        records : Any, optional
            An optional parameter specifying the records (elements) of the Parameter symbol.

        domain_forwarding : bool, optional
            A boolean indicating whether domain forwarding is enabled for the Parameter symbol, by default False

        description : str, optional
            A description or comment for the Parameter symbol.

        uels_on_axes : bool, optional
            A boolean indicating whether unique element lists (UELs) are used as axis values in the symbol, by default False

        Returns
        -------
        Parameter
            The Parameter symbol that was added or updated in the Container.

        Raises
        ------
        ValueError
            If an attempt is made to update an existing Parameter symbol with conflicting properties.
        TypeError
            If 'domain' is not of type list, Set, or str.
        TypeError
            If 'is_singleton' is not of type bool.
        TypeError
            If 'domain_forwarding' is not of type bool.
        TypeError
            If 'uels_on_axes' is not of type bool.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> a = m.addParameter("a", records=5)
        >>> print(a.toValue())
        5.0

        """
        # allows overwriting
        return Parameter(
            self,
            name,
            domain,
            records,
            domain_forwarding,
            description,
            uels_on_axes,
        )

    def addVariable(
        self,
        name: str,
        type: str = "free",
        domain: Optional[List[Union[str, "Set"]]] = None,
        records: Optional[Any] = None,
        domain_forwarding: bool = False,
        description: str = "",
        uels_on_axes: bool = False,
    ) -> "Variable":
        """
        Add a Variable symbol to the Container or update an existing Variable symbol.

        Parameters
        ----------
        name : str
            The name of the Variable symbol to be added or updated.

        type : str, optional
            The type of the Variable symbol, by default "free"

        domain : List[Set | str], optional
            An optional parameter specifying the domain (index set) of the Variable symbol, by default None

        records : Any, optional
            An optional parameter specifying the records (elements) of the Variable symbol.

        domain_forwarding : bool, optional
            A boolean indicating whether domain forwarding is enabled for the Variable symbol, by default False

        description : str, optional
            A description or comment for the Variable symbol.

        uels_on_axes : bool, optional
            A boolean indicating whether unique element lists (UELs) are used as axis values in the symbol, by default False

        Returns
        -------
        Variable
            The Variable object that was added or updated in the Container.

        Raises
        ------
        ValueError
            If an attempt is made to update an existing Variable symbol with conflicting properties.
        TypeError
            If 'domain' is not of type list, Set, or str.
        TypeError
            If 'is_singleton' is not of type bool.
        TypeError
            If 'domain_forwarding' is not of type bool.
        TypeError
            If 'uels_on_axes' is not of type bool.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = m.addSet("i", records=['i1','i2'])
        >>> v = m.addVariable("a", domain=[i])
        >>> print(v.domain[0] == m["i"])
        True

        """
        # allows overwriting
        return Variable(
            self,
            name,
            type,
            domain,
            records,
            domain_forwarding,
            description,
            uels_on_axes,
        )

    def addEquation(
        self,
        name: str,
        type: str = "regular",
        domain: Optional[List[Union["Set", str]]] = None,
        records: Optional[Any] = None,
        domain_forwarding: bool = False,
        description: str = "",
        uels_on_axes: bool = False,
    ) -> "Equation":
        """
        Add an Equation symbol to the Container or update an existing Equation symbol.

        Parameters
        ----------
        name : str
            The name of the Equation symbol to be added or updated.

        type : str, optional
            The type of the Equation symbol, by default "free"

        domain : List[Set | str], optional
            An optional parameter specifying the domain (index set) of the Equation symbol, by default None

        records : Any, optional
            An optional parameter specifying the records (elements) of the Equation symbol.

        domain_forwarding : bool, optional
            A boolean indicating whether domain forwarding is enabled for the Equation symbol, by default False

        description : str, optional
            A description or comment for the Equation symbol.

        uels_on_axes : bool, optional
            A boolean indicating whether unique element lists (UELs) are used as axis values in the symbol, by default False

        Returns
        -------
        Equation
            The Equation object that was added or updated in the Container.


        """
        # allows overwriting
        return Equation(
            self,
            name,
            type,
            domain,
            records,
            domain_forwarding,
            description,
            uels_on_axes,
        )

    def addAlias(self, name: str, alias_with: "Set") -> "Alias":
        """
        Adds an Alias to the Container.

        Parameters
        ----------
        name : str
            The name of the Alias symbol
        alias_with : Set
            The Set to alias

        Returns
        -------
        Alias
            The Alias object that was added

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = m.addSet("i", records=['i1','i2'])
        >>> j = m.addAlias("j", i)
        >>> print(j.getUELs())
        ['i1', 'i2']

        """
        # allows overwriting
        return Alias(self, name, alias_with)

    def addUniverseAlias(self, name: str) -> "UniverseAlias":
        """
        Add a Universe Alias to the Container

        Parameters
        ----------
        name : str
            The name of the Universe Alias symbol

        Returns
        -------
        UniverseAlias
            The Universe Alias object that was added

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = m.addSet("i", records=['i1','i2'])
        >>> j = m.addSet("j", records=['j1','j2','j3'])
        >>> ij = m.addUniverseAlias("ij")
        >>> print(ij.getUELs())
        ['i1', 'i2', 'j1', 'j2', 'j3']

        """
        # allows overwriting
        return UniverseAlias(self, name)

    def _gdx_read(self, load_from, symbols, records, mode, encoding):
        return io.gdx.container_read(self, load_from, symbols, records, mode, encoding)

    def _gdx_write(self, write_to, symbols, uel_priority, compress, mode, eps_to_zero):
        return io.gdx.container_write(
            self, write_to, symbols, uel_priority, compress, mode, eps_to_zero
        )

    def _gmd_read(self, load_from, symbols, records, mode, encoding):
        return io.gmd.container_read(self, load_from, symbols, records, mode, encoding)

    def _gmd_write(
        self, write_to, symbols, uel_priority, merge_symbols, mode, eps_to_zero
    ):
        return io.gmd.container_write(
            self,
            write_to,
            symbols,
            uel_priority,
            merge_symbols,
            mode,
            eps_to_zero,
        )

    def _container_read(self, load_from, symbols, records):
        return io.containers.read(self, load_from, symbols, records)

    def write(
        self,
        write_to: Union["GamsDatabase", os.PathLike, str],
        symbols: Optional[Union[List[str], str]] = None,
        compress: bool = False,
        uel_priority: Optional[Union[List[str], str]] = None,
        merge_symbols: Optional[Union[List[str], str]] = None,
        mode: Optional[str] = None,
        eps_to_zero: bool = True,
    ) -> None:
        """
        Write data from the Container to a GDX or GMD file.

        Parameters
        ----------
        write_to : GamsDatabase | PathLike | str
            The destination where the data should be written.

        symbols : List[str] | str, optional
            An optional parameter specifying the symbols to be written, by default None

        compress : bool, optional
            A boolean indicating whether to compress the GDX file, by default False

        uel_priority : List[str] | str, optional
            An optional parameter specifying the UEL (Unique Element List) priority, by default None

        merge_symbols : List[str] | str, optional
            An optional parameter specifying symbols to merge when writing to a GMD object, by default None

        mode : Optional[str], optional
            An optional parameter specifying the writing mode, by default None

        Raises
        ------
        TypeError
            If 'symbols' is not of type str, list, or NoneType.
        TypeError
            If 'compress' is not of type bool.
        TypeError
            If 'uel_priority' is not of type str, list, or NoneType.
        TypeError
            If 'merge_symbols' is not of type str, list, or NoneType.
        TypeError
            If 'mode' is not of type str or NoneType.
        ValueError
            If 'write_to' is not a valid destination (GamsDatabase, GDX file path, or GMD object).
        ValueError
            If 'mode' is not one of the valid values ("string", "category", or None).
        """
        # check symbols argument
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type str, list or NoneType")

        if isinstance(symbols, str):
            symbols = [symbols]

        if symbols is not None:
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        # check compress argument
        if not isinstance(compress, bool):
            raise TypeError(
                "Argument 'compress' must be of type bool; default "
                "False (no compression); ignored if writing to a GMD object."
            )

        # check eps_to_zero
        if not isinstance(eps_to_zero, bool):
            raise TypeError("Argument 'eps_to_zero' must be type bool")

        # check uel_priority argument
        if not isinstance(uel_priority, (str, list, type(None))):
            raise TypeError(
                "Argument 'uel_priority' must be type str, list or NoneType"
            )

        if isinstance(uel_priority, str):
            uel_priority = [uel_priority]

        # check merge_symbols argument
        if not isinstance(merge_symbols, (str, list, type(None))):
            raise TypeError(
                "Argument 'merge_symbols' must be type str, list or NoneType"
            )

        if isinstance(merge_symbols, str):
            merge_symbols = [merge_symbols]

        if merge_symbols is None:
            merge_symbols = []

        if isinstance(merge_symbols, list):
            if any(not isinstance(i, str) for i in merge_symbols):
                raise TypeError("Argument 'merge_symbols' must contain only type str")

        # check mode argument
        if not isinstance(mode, (str, type(None))):
            raise TypeError("Argument 'mode' must be type str or NoneType")

        if mode is None:
            mode = "category"
        else:
            mode = mode.casefold()
            if mode not in ["string", "category"]:
                raise ValueError(
                    "Argument 'mode' must be `string`, `category` or `None`"
                )

        #
        # figure out data write_to type
        if isinstance(write_to, GamsDatabase):
            dest = DestinationType.GMD
            write_to = write_to._gmd

        elif isinstance(write_to, (os.PathLike, str)):
            fpath = pathlib.Path(write_to)

            if not os.fspath(fpath.expanduser().resolve()).casefold().endswith(".gdx"):
                raise Exception(
                    "Unexpected file type passed to 'write_to' argument "
                    "-- expected file extension '.gdx'"
                )

            dest = DestinationType.GDX
            write_to = os.fspath(fpath.expanduser().resolve())

        else:
            # try GMD, if not, then mark as unknown
            try:
                ret = gmd.gmdInfo(write_to, gmd.GMD_NRSYMBOLSWITHALIAS)
                assert ret[0] == 1
                dest = DestinationType.GMD
            except:
                dest = DestinationType.UNKNOWN

        # throw error if user wants to merge symbols but write_to is not a GMD object
        if dest is DestinationType.GDX and len(merge_symbols) != 0:
            raise Exception(
                "Symbol merge operations are only possible when writing to a"
                " valid GMD object."
            )

        #
        # test and write to different destinations
        #
        if dest is DestinationType.UNKNOWN:
            raise TypeError(
                "Argument 'write_to' expects "
                "type str or Pathlike object (i.e., a path to a GDX file) "
                "or a valid gmdHandle (or GamsDatabase instance) "
                f"User passed: '{type(write_to)}'."
            )

        if dest is DestinationType.GDX:
            self._gdx_write(
                write_to, symbols, uel_priority, compress, mode, eps_to_zero
            )

        if dest is DestinationType.GMD:
            self._gmd_write(
                write_to,
                symbols,
                uel_priority,
                merge_symbols,
                mode,
                eps_to_zero,
            )
