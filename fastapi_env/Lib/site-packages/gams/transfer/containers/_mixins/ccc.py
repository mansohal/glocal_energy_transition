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
from collections.abc import Iterable
import pandas as pd
from gams.control import GamsDatabase
from gams.core import gmd
from gams.transfer._internals import (
    SourceType,
    EQU_TYPE,
    TRANSFER_TO_GAMS_VARIABLE_SUBTYPES,
    TRANSFER_TO_GAMS_EQUATION_SUBTYPES,
)
import gams.transfer._abcs as abcs
from typing import Optional, Union, List, Dict, Sequence


class CCCMixin:
    @property
    def data(self) -> Dict[str, "abcs.AnyContainerSymbol"]:
        return self._data

    @data.setter
    def data(self, data) -> None:
        """Dictionary of symbols where keys are symbol names and values are symbol objects"""
        self._data = data

    def __len__(self):
        return len(self.data)

    def isValid(
        self,
        symbols: Optional[Union[str, List[str]]] = None,
        verbose: bool = False,
        force: bool = False,
    ) -> bool:
        """
        Check the validity of symbols in the Container.

        This method checks the validity of symbols in the Container to ensure that they are consistent and correctly defined. It can check the validity of specific symbols or all symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            A list of symbol names or a single symbol name to be checked for validity. If None, all symbols in the Container will be checked.

        verbose : bool, by default False
            A boolean flag indicating whether to raise an exception if an invalid symbol is found. If True, an exception is raised; if False, the method returns False for invalid symbols.

        force : bool, by default False
            A boolean flag indicating whether to force a recheck of the symbols' validity.

        Returns
        -------
        bool
            Returns True if specified symbols (or all symbols in the Container) are valid. If any symbol is invalid and verbose is False, it returns False. If verbose is True, an exception is raised for the first invalid symbol encountered.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type list or NoneType")

        if symbols is None:
            cache = True
            symbols = list(self.data.keys())
        else:
            cache = False

        if isinstance(symbols, str):
            symbols = [symbols]

        if isinstance(symbols, list):
            if any(not isinstance(i, str) for i in symbols):
                raise TypeError("Argument 'symbols' must contain only type str")

        if not isinstance(verbose, bool):
            raise ValueError("Argument 'verbose' must be type bool")

        if not isinstance(force, bool):
            raise ValueError("Argument 'force' must be type bool")

        if force:
            self._requires_state_check = True

        if self._requires_state_check:
            try:
                self._assert_is_valid(symbols)

                if not cache:
                    self._requires_state_check = True

                return True
            except Exception as err:
                if verbose:
                    raise err
                return False
        else:
            return True

    def listSymbols(self, is_valid: Optional[bool] = None) -> List[str]:
        """
        Get a list of symbol names in the Container.

        This method returns a list of symbol names that are stored in the Container. You can optionally filter the list based on the validity of the symbols.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of symbols. If None (default), all symbols in the Container are returned.
            - If True, only valid symbols are included in the list.
            - If False, only invalid symbols are included in the list.

        Returns
        -------
        List[str]
            A list of symbol names in the Container.

        Raises
        ------
        TypeError
            If the 'is_valid' argument is not of type bool or NoneType.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = gt.Set(m, name="i", records=["seattle", "san-diego"])
        >>> j = gt.Set(m, name="j", records=["new-york", "chicago", "topeka"])
        >>> a = gt.Parameter(m, name="a", domain=[i], records=[["seattle", 350], ["san-diego", 600]])
        >>> b = gt.Parameter(m, name="b", domain=[j], records=[["new-york", 325], ["chicago", 300], ["topeka", 275]])
        >>> print(m.listSymbols())
        ['i', 'j', 'a', 'b']
        """
        if not isinstance(is_valid, (bool, type(None))):
            raise TypeError("Argument 'is_valid' must be type bool or NoneType")

        if is_valid is True:
            return [symname for symname, symobj in self if symobj.isValid()]
        elif is_valid is False:
            return [symname for symname, symobj in self if not symobj.isValid()]
        else:
            return [symname for symname, symobj in self]

    def listParameters(self, is_valid: Optional[bool] = None) -> List[str]:
        """
        Get a list of parameter names in the Container.

        This method returns a list of parameter names that are stored in the Container. You can optionally filter the list based on the validity of the parameters.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of parameters. If None (default), all parameters in the Container are returned.
            - If True, only valid parameters are included in the list.
            - If False, only invalid parameters are included in the list.

        Returns
        -------
        List[str]
            A list of parameter names in the Container, optionally filtered by validity.

        Raises
        ------
        TypeError
            If the 'is_valid' argument is not of type bool or NoneType.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = gt.Set(m, name="i", records=["seattle", "san-diego"])
        >>> j = gt.Set(m, name="j", records=["new-york", "chicago", "topeka"])
        >>> a = gt.Parameter(m, name="a", domain=[i], records=[["seattle", 350], ["san-diego", 600]])
        >>> b = gt.Parameter(m, name="b", domain=[j], records=[["new-york", 325], ["chicago", 300], ["topeka", 275]])
        >>> print(m.listParameters())
        ['a', 'b']

        """
        if not isinstance(is_valid, (bool, type(None))):
            raise TypeError("Argument 'is_valid' must be type bool or NoneType")

        return [
            symobj.name
            for symobj in self.getSymbols(self.listSymbols(is_valid))
            if isinstance(symobj, abcs.ABCParameter)
        ]

    def listSets(self, is_valid: Optional[bool] = None) -> List[str]:
        """
        Get a list of set names in the Container.

        This method returns a list of set names that are stored in the Container. You can optionally filter the list based on the validity of the sets.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of sets. If None (default), all sets in the Container are returned.
            - If True, only valid sets are included in the list.
            - If False, only invalid sets are included in the list.

        Returns
        -------
        List[str]
            A list of set names in the Container, optionally filtered by validity.

        Raises
        ------
        TypeError
            If the 'is_valid' argument is not of type bool or NoneType.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = gt.Set(m, name="i", records=["seattle", "san-diego"])
        >>> j = gt.Set(m, name="j", records=["new-york", "chicago", "topeka"])
        >>> a = gt.Parameter(m, name="a", domain=[i], records=[["seattle", 350], ["san-diego", 600]])
        >>> b = gt.Parameter(m, name="b", domain=[j], records=[["new-york", 325], ["chicago", 300], ["topeka", 275]])
        >>> print(m.listSets())
        ['i', 'j']

        """
        if not isinstance(is_valid, (bool, type(None))):
            raise TypeError("Argument 'is_valid' must be type bool or NoneType")

        return [
            symobj.name
            for symobj in self.getSymbols(self.listSymbols(is_valid))
            if isinstance(symobj, abcs.ABCSet)
        ]

    def listAliases(self, is_valid: Optional[bool] = None) -> List[str]:
        """
        Get a list of alias names in the Container.

        This method returns a list of alias names that are stored in the Container. You can optionally filter the list based on the validity of the aliases.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of aliases. If None (default), all aliases in the Container are returned.
            - If True, only valid aliases are included in the list.
            - If False, only invalid aliases are included in the list.

        Returns
        -------
        List[str]
            A list of alias names in the Container, optionally filtered by validity.

        Raises
        ------
        TypeError
            If the 'is_valid' argument is not of type bool or NoneType.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> plants = gt.Set(m, name="plants", records=["seattle", "san-diego"])
        >>> markets = gt.Set(m, name="markets", records=["new-york", "chicago", "topeka"])
        >>> i = gt.Alias(m, name="i", alias_with=plants)
        >>> j = gt.Alias(m, name="j", alias_with=markets)
        >>> a = gt.Parameter(m, name="a", domain=[i], records=[["seattle", 350], ["san-diego", 600]])
        >>> b = gt.Parameter(m, name="b", domain=[j], records=[["new-york", 325], ["chicago", 300], ["topeka", 275]])
        >>> print(m.listAliases())
        ['i', 'j']

        """
        if not isinstance(is_valid, (bool, type(None))):
            raise TypeError("Argument 'is_valid' must be type bool or NoneType")

        return [
            symobj.name
            for symobj in self.getSymbols(self.listSymbols(is_valid))
            if isinstance(symobj, (abcs.ABCAlias, abcs.ABCUniverseAlias))
        ]

    def listVariables(
        self,
        is_valid: Optional[bool] = None,
        types: Optional[Union[str, List[str]]] = None,
    ) -> List[str]:
        """
        Get a list of variable names in the Container.

        This method returns a list of variable names that are stored in the Container. You can optionally filter the list based on the validity and type of the variables.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of variables based on their validity.
            - If True, only valid variables are included in the list.
            - If False, only invalid variables are included in the list.
            - If None (default), all variables are included in the list.

        types : str | List[str], optional
            An optional string or list of strings specifying the types of variables to include in the list.
            - If None (default), all variable types are included in the list.
            - If a string or list of strings is provided, only variables of the specified types are included in the list.

        Returns
        -------
        List[str]
            A list of variable names in the Container, optionally filtered by validity and type.

        Raises
        ------
        TypeError
            If the 'is_valid' argument is not of type bool or NoneType, or if the 'types' argument is not of type str, list, or NoneType.
        ValueError
            If the 'types' argument contains unrecognized variable types.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = gt.Set(m, name="i", records=["seattle", "san-diego"])
        >>> j = gt.Set(m, name="j", records=["new-york", "chicago", "topeka"])
        >>> a = gt.Parameter(m, name="a", domain=[i], records=[["seattle", 350], ["san-diego", 600]])
        >>> b = gt.Parameter(m, name="b", domain=[j], records=[["new-york", 325], ["chicago", 300], ["topeka", 275]])
        >>> x = gt.Variable(m, name="x", domain=[i, j], type="positive")
        >>> z = gt.Variable(m, name="z", type="free")
        >>> print(m.listVariables())
        ['x', 'z']
        >>> print(m.listVariables(types="free"))
        ['z']

        """
        if not isinstance(is_valid, (bool, type(None))):
            raise TypeError("Argument 'is_valid' must be type bool or NoneType")

        if not isinstance(types, (str, list, type(None))):
            raise TypeError("Argument 'types' must be type str, list, or NoneType")

        if types is None:
            return [
                symobj.name
                for symobj in self.getSymbols(self.listSymbols(is_valid))
                if isinstance(symobj, abcs.ABCVariable)
            ]

        else:
            if isinstance(types, str):
                types = [types]

            # casefold to allow mixed case matching
            types = [i.casefold() for i in types]

            if any(i not in TRANSFER_TO_GAMS_VARIABLE_SUBTYPES.keys() for i in types):
                raise ValueError(
                    "User input unrecognized variable type, "
                    f"variable types can only take: {list(TRANSFER_TO_GAMS_VARIABLE_SUBTYPES.keys())}"
                )

            return [
                symobj.name
                for symobj in self.getSymbols(self.listSymbols(is_valid))
                if isinstance(symobj, abcs.ABCVariable) and symobj.type in types
            ]

    def listEquations(
        self,
        is_valid: Optional[bool] = None,
        types: Optional[Union[str, List[str]]] = None,
    ) -> List[str]:
        """
        Get a list of equation names in the Container.

        This method returns a list of equation names that are stored in the Container. You can optionally filter the list based on the validity and type of the equations.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of equations based on their validity.
            - If True, only valid equations are included in the list.
            - If False, only invalid equations are included in the list.
            - If None (default), all equations are included in the list.

        types : str | List[str], optional
            An optional string or list of strings specifying the types of equations to include in the list.
            - If None (default), all equation types are included in the list.
            - If a string or list of strings is provided, only equations of the specified types are included in the list.

        Returns
        -------
        List[str]
            A list of equation names in the Container, optionally filtered by validity and type.

        Raises
        ------
        TypeError
            If the 'is_valid' argument is not of type bool or NoneType, or if the 'types' argument is not of type str, list, or NoneType.
        ValueError
            If the 'types' argument contains unrecognized equation types.

        Examples
        --------
        >>> import gams.transfer as gt
        >>> m = gt.Container()
        >>> i = gt.Set(m, name="i", records=["seattle", "san-diego"])
        >>> j = gt.Set(m, name="j", records=["new-york", "chicago", "topeka"])
        >>> a = gt.Parameter(m, name="a", domain=[i], records=[["seattle", 350], ["san-diego", 600]])
        >>> b = gt.Parameter(m, name="b", domain=[j], records=[["new-york", 325], ["chicago", 300], ["topeka", 275]])
        >>> x = gt.Variable(m, name="x", domain=[i, j], type="positive")
        >>> z = gt.Variable(m, name="z", type="free")
        >>> cost = gt.Equation(m, name="cost", type="eq")
        >>> supply = gt.Equation(m, name="supply", type="leq", domain=[i])
        >>> demand = gt.Equation(m, name="demand", type="geq", domain=[j])
        >>> print(m.listEquations())
        ['cost', 'supply', 'demand']
        >>> print(m.listEquations(types="geq"))
        ['demand']

        """
        if not isinstance(is_valid, (bool, type(None))):
            raise TypeError("Argument 'is_valid' must be type bool or NoneType")

        if not isinstance(types, (str, list, type(None))):
            raise TypeError("Argument 'types' must be type str, list, or NoneType")

        if types is None:
            return [
                symobj.name
                for symobj in self.getSymbols(self.listSymbols(is_valid))
                if isinstance(symobj, abcs.ABCEquation)
            ]

        else:
            if isinstance(types, str):
                types = [types]

            # casefold to allow mixed case matching (and extended syntax)
            types = [EQU_TYPE[i.casefold()] for i in types]

            if any(i not in TRANSFER_TO_GAMS_EQUATION_SUBTYPES.keys() for i in types):
                raise ValueError(
                    "User input unrecognized variable type, "
                    f"variable types can only take: {list(TRANSFER_TO_GAMS_EQUATION_SUBTYPES.keys())}"
                )

            return [
                symobj.name
                for symobj in self.getSymbols(self.listSymbols(is_valid))
                if isinstance(symobj, abcs.ABCEquation) and symobj.type in types
            ]

    def read(
        self,
        load_from: Union["GamsDatabase", os.PathLike, str, "abcs.ABCContainer"],
        symbols: Optional[Union[str, List[str]]] = None,
        records: bool = True,
        mode: Optional[str] = None,
        encoding: Optional[str] = None,
    ):
        """
        Read data into the Container from various sources.

        This method reads data into the Container from different data sources, such as GDX files, GMD objects, or other Containers. It provides flexibility in reading and loading data into the Container.

        Parameters
        ----------
        load_from : GamsDatabase | os.PathLike | str | abcs.ABCContainer
            The data source to read from. It can be one of the following:
            - A GamsDatabase instance to read data from a GAMS database.
            - A path to a GDX file (str or os.PathLike) to read data from a GDX file.
            - A GMD object (gmdHandle) to read data from a GMD object.
            - Another Container instance to copy data from.

        symbols : str | List[str], optional
            An optional list of symbol names to read from the data source. If None (default), all symbols are read.
            You can provide a single symbol name as a string or a list of symbol names as a list of strings.

        records : bool, default=True
            A boolean flag indicating whether to read symbol records (data values) from the data source.
            - If True, symbol records are read.
            - If False, symbol records are not read, only the symbol metadata is loaded.

        mode : str, optional
            An optional string specifying the read mode when reading data

        encoding : str, optional
            An optional string specifying the character encoding to use when reading data from GMD objects.
            If None (default), the default system encoding is used.

        Raises
        ------
        TypeError
            - If the 'records' argument is not of type bool.
            - if the 'symbols' argument is not of type str, list, or NoneType.
            - if the 'mode' argument is not of type str.
            - if the 'encoding' argument is not of type str or NoneType.

        Exception
            - If the 'load_from' argument is of an unsupported type.
            - if the file specified by 'load_from' does not exist.
        """
        if not isinstance(records, bool):
            raise TypeError("Argument 'records' must be type bool")

        if not isinstance(symbols, (list, str, type(None))):
            raise TypeError("Argument 'symbols' must be type str, list, or NoneType")

        if isinstance(symbols, str):
            symbols = [symbols]

        if symbols is not None:
            if any(not isinstance(i, str) for i in symbols):
                raise Exception("Argument 'symbols' must contain only type str")

        if mode is None:
            mode = "category"

        if not isinstance(mode, str):
            raise TypeError("Argument 'mode' must be type str (`string` or `category`)")

        if not isinstance(encoding, (str, type(None))):
            raise TypeError("Argument 'encoding' must be type str or NoneType")

        #
        # figure out data source type
        if isinstance(load_from, GamsDatabase):
            source = SourceType.GMD
            load_from = load_from._gmd

        elif isinstance(load_from, (os.PathLike, str)):
            fpath = pathlib.Path(load_from)

            if not fpath.expanduser().exists():
                raise Exception(
                    f"GDX file '{os.fspath(fpath.expanduser().resolve())}' does not exist, "
                    "check filename spelling or path specification"
                )

            if not os.fspath(fpath.expanduser().resolve()).casefold().endswith(".gdx"):
                raise Exception(
                    "Unexpected file type passed to 'load_from' argument "
                    "-- expected file extension '.gdx'"
                )

            source = SourceType.GDX
            load_from = os.fspath(fpath.expanduser().resolve())

        elif isinstance(load_from, abcs.ABCContainer):
            source = SourceType.CONTAINER

        else:
            # try GMD, if not, then mark as unknown
            try:
                ret = gmd.gmdInfo(load_from, gmd.GMD_NRSYMBOLSWITHALIAS)
                assert ret[0] == 1
                source = SourceType.GMD
            except:
                source = SourceType.UNKNOWN

        #
        # test for valid source
        if source is SourceType.UNKNOWN:
            raise TypeError(
                "Argument 'load_from' expects "
                "type str or PathLike (i.e., a path to a GDX file) "
                ", a valid gmdHandle (or GamsDatabase instance) "
                ", an instance of another Container "
                ", User passed: "
                f"'{type(load_from)}'."
            )

        #
        # read different types
        if source is SourceType.GDX:
            self._gdx_read(load_from, symbols, records, mode, encoding)

        elif source is SourceType.GMD:
            self._gmd_read(load_from, symbols, records, mode, encoding)

        elif source is SourceType.CONTAINER:
            self._container_read(load_from, symbols, records)

    def describeSets(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> Union[pd.DataFrame, None]:
        """
        Generate a DataFrame describing sets within the Container.

        This method creates a DataFrame that provides descriptive information about sets within the Container.
        You can specify the sets to describe using the 'symbols' parameter. If 'symbols' is None (default), all sets are described.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying which sets to describe.

        Returns
        -------
        DataFrame | None
            A Pandas DataFrame containing descriptive information about the specified sets.
            The DataFrame includes the following columns:
            - 'name': The name of the set.
            - 'is_singleton': Whether the set is a singleton set (True) or not (False).
            - 'domain': The domain of the set.
            - 'domain_type': The type of the set's domain.
            - 'dimension': The dimension of the set.
            - 'number_records': The number of records (size) of the set.
            - 'sparsity': The sparsity of the set.

            If 'symbols' includes alias sets, the DataFrame will also contain the following additional columns:
            - 'is_alias': Whether the set is an alias set (True) or not (False).
            - 'alias_with': The name of the set that the alias set is associated with (if it is an alias set).

            The DataFrame is sorted by set name in ascending order.

        Raises
        ------
        TypeError
            If the 'symbols' argument is not of type str, list, or NoneType.
            If 'symbols' contains elements that are not of type str.

        Notes
        -----
        - This method generates a descriptive summary of sets within the Container, including their properties and characteristics.
        - The 'symbols' parameter allows you to specify which sets to describe. If None (default), all sets are described.
        - The resulting DataFrame provides insights into each set's attributes, such as dimensionality, size, and sparsity.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type str, list, or NoneType")

        if symbols is None:
            symbols = self.listSets()

        if isinstance(symbols, str):
            symbols = [symbols]

        if any(not isinstance(i, str) for i in symbols):
            raise TypeError("Argument 'symbols' must only contain type str")

        # check for isValid
        for symobj in self.getSymbols(symbols):
            if not symobj.isValid():
                raise Exception(
                    f"Cannot generate describe table because symbol `{symobj.name}` "
                    "is currently invalid. Use `<symbol>.isValid(verbose=True)` to debug."
                )

        dfs = []
        cols = [
            "name",
            "is_singleton",
            "domain",
            "domain_type",
            "dimension",
            "number_records",
            "sparsity",
        ]

        # find all sets and aliases
        all_sets = self.listSets()
        all_aliases = self.listAliases()
        all_sets_aliases = all_sets + all_aliases

        data = []
        for i in symbols:
            if i in all_sets_aliases:
                data.append(
                    (
                        i,
                        self[i].is_singleton,
                        self[i].domain_names,
                        self[i].domain_type,
                        self[i].dimension,
                        self[i].number_records,
                        self[i].getSparsity(),
                    )
                )

        # create dataframe
        if data != []:
            df = pd.DataFrame(data, columns=cols)

            if any(i in all_aliases for i in symbols):
                df_is_alias = []
                df_alias_with = []

                for i in symbols:
                    if i in all_sets_aliases:
                        df_is_alias.append(
                            isinstance(self[i], (abcs.ABCAlias, abcs.ABCUniverseAlias))
                        )

                        if isinstance(self[i], abcs.ABCAlias):
                            df_alias_with.append(self[i].alias_with.name)
                        elif isinstance(self[i], abcs.ABCUniverseAlias):
                            df_alias_with.append(self[i].alias_with)
                        else:
                            df_alias_with.append(None)

                # add in is_alias column
                df.insert(2, "is_alias", pd.Series(df_is_alias, dtype=bool))
                df.insert(3, "alias_with", pd.Series(df_alias_with, dtype=object))

            return df.round(3).sort_values(by="name", ignore_index=True)
        else:
            return None

    def describeAliases(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> Union[pd.DataFrame, None]:
        """
        Generate a DataFrame describing alias symbols in the Container.

        This method generates a DataFrame providing detailed information about alias symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the alias symbol names to describe. If None (default), Describe all alias symbols in the Container.

        Returns
        -------
        DataFrame | None
            A pandas DataFrame containing the description of alias symbols that match the specified symbol names.
            If no matching alias symbols are found, None is returned.

        Raises
        ------
        ValueError
            - If the 'symbols' argument is not of type str, list, or NoneType.
            - If an alias symbol name specified in 'symbols' does not exist in the Container.

        Notes
        -----
        - This method provides a tabular summary of alias symbols, including information such as alias relationships, dimension, sparsity, etc.
        - The 'symbols' parameter allows you to describe one or more alias symbols in the Container.
        - If 'symbols' is None (default), the method describes all alias symbols in the Container.
        - The method raises a ValueError if any alias symbol name specified in 'symbols' does not exist in the Container.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type str, list, or NoneType")

        if symbols is None:
            symbols = self.listAliases()

        if isinstance(symbols, str):
            symbols = [symbols]

        if any(not isinstance(i, str) for i in symbols):
            raise TypeError("Argument 'symbols' must only contain type str")

        # check for isValid
        for symobj in self.getSymbols(symbols):
            if not symobj.isValid():
                raise Exception(
                    f"Cannot generate describe table because symbol `{symobj.name}` "
                    "is currently invalid. Use `<symbol>.isValid(verbose=True)` to debug."
                )

        dfs = []
        cols = [
            "name",
            "alias_with",
            "is_singleton",
            "domain",
            "domain_type",
            "dimension",
            "number_records",
            "sparsity",
        ]

        # find aliases
        all_aliases = self.listAliases()

        data = []
        for i in symbols:
            if i in all_aliases:
                if isinstance(self[i], abcs.ABCAlias):
                    alias_name = self[i].alias_with.name
                elif isinstance(self[i], abcs.ABCUniverseAlias):
                    alias_name = self[i].alias_with
                else:
                    raise Exception("Encountered unknown symbol type")

                data.append(
                    (
                        i,
                        alias_name,
                        self[i].is_singleton,
                        self[i].domain_names,
                        self[i].domain_type,
                        self[i].dimension,
                        self[i].number_records,
                        self[i].getSparsity(),
                    )
                )

        if data != []:
            return (
                pd.DataFrame(data, columns=cols)
                .round(3)
                .sort_values(by="name", ignore_index=True)
            )
        else:
            return None

    def describeParameters(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> Union[pd.DataFrame, None]:
        """
        Generate a DataFrame describing parameter symbols in the Container.

        This method generates a DataFrame providing detailed information about parameter symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the parameter symbol names to describe. If None (default), Describe all parameter symbols in the Container.

        Returns
        -------
        DataFrame | None
            A pandas DataFrame containing the description of parameter symbols that match the specified symbol names.
            If no matching parameter symbols are found, None is returned.

        Raises
        ------
        ValueError
            - If the 'symbols' argument is not of type str, iterable, or NoneType.
            - If a parameter symbol name specified in 'symbols' does not exist in the Container.

        Notes
        -----
        - This method provides a tabular summary of parameter symbols, including information such as domain, dimension, sparsity, etc.
        - The 'symbols' parameter allows you to describe one or more parameter symbols in the Container.
        - If 'symbols' is None (default), the method describes all parameter symbols in the Container.
        - The method raises a ValueError if any parameter symbol name specified in 'symbols' does not exist in the Container.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type str, list, or NoneType")

        if symbols is None:
            symbols = self.listParameters()

        if isinstance(symbols, str):
            symbols = [symbols]

        if any(not isinstance(i, str) for i in symbols):
            raise TypeError("Argument 'symbols' must only contain type str")

        # check for isValid
        for symobj in self.getSymbols(symbols):
            if not symobj.isValid():
                raise Exception(
                    f"Cannot generate describe table because symbol `{symobj.name}` "
                    "is currently invalid. Use `<symbol>.isValid(verbose=True)` to debug."
                )

        dfs = []
        cols = [
            "name",
            "domain",
            "domain_type",
            "dimension",
            "number_records",
            "min",
            "mean",
            "max",
            "where_min",
            "where_max",
            "sparsity",
        ]

        # find all parameters
        all_parameters = self.listParameters()

        data = []
        for i in symbols:
            if i in all_parameters:
                data.append(
                    (
                        i,
                        self[i].domain_names,
                        self[i].domain_type,
                        self[i].dimension,
                        self[i].number_records,
                        self[i].getMinValue(),
                        self[i].getMeanValue(),
                        self[i].getMaxValue(),
                        self[i].whereMin(),
                        self[i].whereMax(),
                        self[i].getSparsity(),
                    )
                )

        if data != []:
            return (
                pd.DataFrame(data, columns=cols)
                .round(3)
                .sort_values(by="name", ignore_index=True)
            )
        else:
            return None

    def describeVariables(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> Union[pd.DataFrame, None]:
        """
        Generate a DataFrame describing variable symbols in the Container.

        This method generates a DataFrame providing detailed information about variable symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the variable symbol names to describe. If None (default), Describe all variable symbols in the Container.

        Returns
        -------
        DataFrame | None
            A pandas DataFrame containing the description of variable symbols that match the specified symbol names.
            If no matching variable symbols are found, None is returned.

        Raises
        ------
        ValueError
        - If the 'symbols' argument is not of type str, iterable, or NoneType.
        - If a variable symbol name specified in 'symbols' does not exist in the Container.

        Notes
        -----
        - This method provides a tabular summary of variable symbols, including information such as type, domain, dimension, sparsity, etc.
        - The 'symbols' parameter allows you to describe one or more variable symbols in the Container.
        - If 'symbols' is None (default), the method describes all variable symbols in the Container.
        - The method raises a ValueError if any variable symbol name specified in 'symbols' does not exist in the Container.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type str, list, or NoneType")

        if symbols is None:
            symbols = self.listVariables()

        if isinstance(symbols, str):
            symbols = [symbols]

        if any(not isinstance(i, str) for i in symbols):
            raise TypeError("Argument 'symbols' must only contain type str")

        # check for isValid
        for symobj in self.getSymbols(symbols):
            if not symobj.isValid():
                raise Exception(
                    f"Cannot generate describe table because symbol `{symobj.name}` "
                    "is currently invalid. Use `<symbol>.isValid(verbose=True)` to debug."
                )

        dfs = []
        cols = [
            "name",
            "type",
            "domain",
            "domain_type",
            "dimension",
            "number_records",
            "sparsity",
            "min_level",
            "mean_level",
            "max_level",
            "where_max_abs_level",
        ]

        # find all variables
        all_variables = self.listVariables()

        data = []
        for i in symbols:
            if i in all_variables:
                data.append(
                    (
                        i,
                        self[i].type,
                        self[i].domain_names,
                        self[i].domain_type,
                        self[i].dimension,
                        self[i].number_records,
                        self[i].getSparsity(),
                        self[i].getMinValue("level"),
                        self[i].getMeanValue("level"),
                        self[i].getMaxValue("level"),
                        self[i].whereMaxAbs("level"),
                    )
                )
        if data != []:
            return (
                pd.DataFrame(data, columns=cols)
                .round(3)
                .sort_values(by="name", ignore_index=True)
            )
        else:
            return None

    def describeEquations(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> Union[pd.DataFrame, None]:
        """
        Generate a DataFrame describing equation symbols in the Container.

        This method generates a DataFrame providing detailed information about equation symbols in the Container.

        Parameters
        ----------
        symbols : str | List[str], optional
            An optional parameter specifying the equation symbol names to describe. If None (default), Describe all equation symbols in the Container.

        Returns
        -------
        DataFrame | None
            A pandas DataFrame containing the description of equation symbols that match the specified symbol names.
            If no matching equation symbols are found, None is returned.

        Raises
        ------
        ValueError
        - If the 'symbols' argument is not of type str, iterable, or NoneType.
        - If an equation symbol name specified in 'symbols' does not exist in the Container.

        Notes
        -----
        - This method provides a tabular summary of equation symbols, including information such as type, domain, dimension, sparsity, etc.
        - The 'symbols' parameter allows you to describe one or more equation symbols in the Container.
        - If 'symbols' is None (default), the method describes all equation symbols in the Container.
        - The method raises a ValueError if any equation symbol name specified in 'symbols' does not exist in the Container.
        """
        if not isinstance(symbols, (str, list, type(None))):
            raise TypeError("Argument 'symbols' must be type str, list, or NoneType")

        if symbols is None:
            symbols = self.listEquations()

        if isinstance(symbols, str):
            symbols = [symbols]

        if any(not isinstance(i, str) for i in symbols):
            raise TypeError("Argument 'symbols' must only contain type str")

        # check for isValid
        for symobj in self.getSymbols(symbols):
            if not symobj.isValid():
                raise Exception(
                    f"Cannot generate describe table because symbol `{symobj.name}` "
                    "is currently invalid. Use `<symbol>.isValid(verbose=True)` to debug."
                )

        dfs = []
        cols = [
            "name",
            "type",
            "domain",
            "domain_type",
            "dimension",
            "number_records",
            "sparsity",
            "min_level",
            "mean_level",
            "max_level",
            "where_max_abs_level",
        ]

        # find all equations
        all_equations = self.listEquations()

        data = []
        for i in symbols:
            if i in all_equations:
                data.append(
                    (
                        i,
                        self[i].type,
                        self[i].domain_names,
                        self[i].domain_type,
                        self[i].dimension,
                        self[i].number_records,
                        self[i].getSparsity(),
                        self[i].getMinValue("level"),
                        self[i].getMeanValue("level"),
                        self[i].getMaxValue("level"),
                        self[i].whereMaxAbs("level"),
                    )
                )

        if data != []:
            return (
                pd.DataFrame(data, columns=cols)
                .round(3)
                .sort_values(by="name", ignore_index=True)
            )
        else:
            return None

    def getSets(self, is_valid: Optional[bool] = None) -> List["abcs.ABCSet"]:
        """
        Retrieve set objects from the Container.

        This method allows you to retrieve set objects from the Container based on their names.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of sets. If None (default), all sets in the Container are returned.
            If True, only valid sets are included in the list.
            If False, only invalid sets are included in the list.

        Returns
        -------
        List[ABCSet]
            A list of set objects that match the specified names.
        """
        return self.getSymbols(self.listSets(is_valid=is_valid))

    def getAliases(self, is_valid: Optional[bool] = None) -> List["abcs.ABCAlias"]:
        """
        Retrieve alias objects from the Container.

        This method allows you to retrieve alias objects from the Container based on their names.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of aliases. If None (default), all aliases in the Container are returned.
            If True, only valid aliases are included in the list.
            If False, only invalid aliases are included in the list.

        Returns
        -------
        List[ABCAlias]
            A list of alias objects that match the specified names.
        """
        return self.getSymbols(self.listAliases(is_valid=is_valid))

    def getParameters(
        self, is_valid: Optional[bool] = None
    ) -> List["abcs.ABCParameter"]:
        """
        Retrieve parameter objects from the Container.

        This method allows you to retrieve parameter objects from the Container based on their names.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of parameters. If None (default), all parameters in the Container are returned.
            If True, only valid parameters are included in the list.
            If False, only invalid parameters are included in the list.

        Returns
        -------
        List[ABCAlias]
            A list of parameter objects that match the specified names.
        """
        return self.getSymbols(self.listParameters(is_valid=is_valid))

    def getVariables(
        self,
        is_valid: Optional[bool] = None,
        types: Optional[Union[str, List[str]]] = None,
    ) -> List["abcs.ABCVariable"]:
        """
        Retrieve variable objects from the Container.

        This method allows you to retrieve variable objects from the Container based on their names.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of variables. If None (default), all variables in the Container are returned.
            If True, only valid variables are included in the list.
            If False, only invalid variables are included in the list.
        types : str | List[str], optional
            An optional string or list of strings specifying the types of variables to include in the list.
            If None (default), all variable types are included in the list.
            If a string or list of strings is provided, only variables of the specified types are included in the list.

        Returns
        -------
        List[ABCVariable]
            A list of variable objects that match the specified names.
        """
        return self.getSymbols(self.listVariables(is_valid=is_valid, types=types))

    def getEquations(
        self,
        is_valid: Optional[bool] = None,
        types: Optional[Union[str, List[str]]] = None,
    ) -> List["abcs.ABCEquation"]:
        """
        Retrieve equation objects from the Container.

        This method allows you to retrieve equation objects from the Container based on their names.

        Parameters
        ----------
        is_valid : bool, optional
            An optional boolean flag used to filter the list of equations. If None (default), all equations in the Container are returned.
            If True, only valid equations are included in the list.
            If False, only invalid equations are included in the list.
        types : str | List[str], optional
            An optional string or list of strings specifying the types of equations to include in the list.
            If None (default), all equation types are included in the list.
            If a string or list of strings is provided, only equations of the specified types are included in the list.

        Returns
        -------
        List[ABCEquation]
            A list of equation objects that match the specified names.
        """
        return self.getSymbols(self.listEquations(is_valid=is_valid, types=types))

    def getSymbols(
        self, symbols: Optional[Union[str, Sequence[str]]] = None
    ) -> List["abcs.AnyContainerSymbol"]:
        """
        Retrieve symbol objects from the Container.

        This method allows you to retrieve symbol objects from the Container based on their names.

        Parameters
        ----------
        symbols : str | Sequence[str], optional
            An optional parameter specifying the symbol names to retrieve. If None (default), Retrieve all symbols stored in the Container.

        Returns
        -------
        List[AnyContainerSymbol]
            A list of symbol objects that match the specified symbol names.

        Raises
        ------
        ValueError
            - If the 'symbols' argument is not of type str, iterable, or NoneType.
            - If a symbol name specified in 'symbols' does not exist in the Container.
        """
        if symbols is None:
            return list(self.data.values())

        if isinstance(symbols, str):
            symbols = [symbols]

        if not isinstance(symbols, Iterable):
            raise ValueError("Argument 'symbols' must be type str or other iterable")

        obj = []
        for symname in symbols:
            try:
                obj.append(self[symname])
            except KeyError as err:
                raise KeyError(f"Symbol `{symname}` does not appear in the Container")
        return obj
