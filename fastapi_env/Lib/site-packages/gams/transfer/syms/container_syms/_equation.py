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

import itertools
import weakref
from gams.core import gdx
from gams.transfer._abcs import ABCSet, ABCEquation, ABCContainer
from gams.transfer.syms._mixins import (
    PVEMixin,
    SAPVEMixin,
    SAUAPVEMixin,
    SPVEMixin,
    VEMixin,
)
from gams.transfer._internals import (
    EQU_DEFAULT_VALUES,
    EQU_TYPE,
    TRANSFER_TO_GAMS_EQUATION_SUBTYPES,
)
from gams.transfer.syms._mixins.pivot import PivotEquationMixin
from gams.transfer.syms._mixins.generateRecords import GenerateRecordsEquationMixin
from gams.transfer.syms._mixins.equals import EqualsEquationMixin
from typing import Any, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from gams.transfer import Container


class Equation(
    PVEMixin,
    SAPVEMixin,
    SAUAPVEMixin,
    SPVEMixin,
    VEMixin,
    PivotEquationMixin,
    GenerateRecordsEquationMixin,
    EqualsEquationMixin,
    ABCEquation,
):
    """
    Represents an Equation symbol in GAMS. https://www.gams.com/latest/docs/UG_Equations.html

    Parameters
    ----------
    container : Container
    name : str
    type : str
    domain : Union[Set, str], optional
    records : Any, optional
    domain_forwarding : bool, optional
    description : str, optional
    uels_on_axes: bool

    Examples
    --------
    >>> import gams.transfer as gt
    >>> m = gt.Container()
    >>> i = gt.Set(m, "i", records=['i1','i2'])
    >>> a = gt.Parameter(m, "a", [i], records=[['i1',1],['i2',2]])
    >>> v = gt.Variable(m, "v", domain=[i])
    >>> e = gt.Equation(m, "e", domain=[i])

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
    is_scalar : bool
        Flag that identifies if the Equation is scalar
    modified: bool
        Flag that identifies if the symbol has been modified
    name : str
        Name of the symbol
    number_records : int
        The number of symbol records
    records : DataFrame
        The main symbol records
    shape : tuple
        Shape of symbol records
    summary : dict
        A dict of only the metadata
    type : str
        Type of the equation
    """

    @classmethod
    def _from_gams(cls, container, name, type, domain, records=None, description=""):
        # create new symbol object
        obj = Equation.__new__(cls)

        # set private properties directly
        obj.type = EQU_TYPE[type]
        obj._gams_type = gdx.GMS_DT_EQU
        obj._gams_subtype = TRANSFER_TO_GAMS_EQUATION_SUBTYPES[type]
        obj._requires_state_check = False
        obj._container = weakref.proxy(container)
        obj._name = name
        obj._domain = domain
        obj._domain_forwarding = False
        obj._description = description
        obj._records = None
        obj._modified = True

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
        type: str,
        domain: Optional[List[Union[ABCSet, str]]] = None,
        records: Optional[Any] = None,
        domain_forwarding: bool = False,
        description: str = "",
        uels_on_axes: bool = False,
    ):
        # domain handling
        if domain is None:
            domain = []

        if isinstance(domain, (ABCSet, str)):
            domain = [domain]

        # does symbol exist
        has_symbol = False
        if isinstance(getattr(self, "container", None), ABCContainer):
            has_symbol = True

        if has_symbol:
            try:
                if self.type != type.casefold():
                    raise TypeError(
                        f"Cannot overwrite symbol in container unless equation types are equal: `{self.type}` != `{type.casefold()}`"
                    )

                if any(
                    d1 != d2 for d1, d2 in itertools.zip_longest(self.domain, domain)
                ):
                    raise ValueError(
                        "Cannot overwrite symbol in container unless symbol domains are equal"
                    )

                if self.domain_forwarding != domain_forwarding:
                    raise ValueError(
                        "Cannot overwrite symbol in container unless 'domain_forwarding' is left unchanged"
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
            self.type = type
            self._gams_type = gdx.GMS_DT_EQU
            self._gams_subtype = TRANSFER_TO_GAMS_EQUATION_SUBTYPES[self.type]
            self._requires_state_check = True
            self.container = container
            self.container._requires_state_check = True
            self.name = name
            self.domain = domain
            self.domain_forwarding = domain_forwarding
            self.description = description
            self.records = None
            self.modified = True

            # only set records if records are provided
            if records is not None:
                self.setRecords(records, uels_on_axes=uels_on_axes)

            # add to container
            container.data.update({name: self})

    def __repr__(self):
        return f"<{self.type.capitalize()} Equation `{self.name}` ({hex(id(self))})>"

    def __delitem__(self):
        del self.container.data[self.name]

    @property
    def default_records(self):
        """Default records of an equation"""
        return EQU_DEFAULT_VALUES[self._type]

    @property
    def type(self) -> str:
        """
        The type of equation;
        1. 'eq', 'E', or '=E=' -- equality
        2. 'geq', 'G', or '=G=' -- greater than or equal to inequality
        3. 'leq', 'L', or '=L=''  -- less than or equal to inequality
        4. 'nonbinding', 'N', or '=N='  -- nonbinding relationship
        5. 'cone', 'C', or '=C=' -- cone equation
        6. 'external', 'X', or '=X=' -- external equation
        7. 'boolean', 'B', or '=B=' -- boolean equation

        Returns
        -------
        str
            The type of equation
        """
        return self._type

    @type.setter
    def type(self, typ: str):
        """
        The type of equation;
        1. 'eq', 'E', or '=E=' -- equality
        2. 'geq', 'G', or '=G=' -- greater than or equal to inequality
        3. 'leq', 'L', or '=L=''  -- less than or equal to inequality
        4. 'nonbinding', 'N', or '=N='  -- nonbinding relationship
        5. 'cone', 'C', or '=C=' -- cone equation
        6. 'external', 'X', or '=X=' -- external equation
        7. 'boolean', 'B', or '=B=' -- boolean equation

        Parameters
        ----------
        typ : str
            _description_
        """
        if not isinstance(typ, str):
            raise TypeError(f"Argument 'type' must be type str")

        typ = typ.casefold()

        if typ not in EQU_TYPE.keys():
            raise ValueError(
                "Argument 'type' must be one of the following (mixed-case OK): \n\n"
                "1. 'eq', 'E', or '=E=' -- equality \n"
                "2. 'geq', 'G', or '=G=' -- greater than or equal to inequality \n"
                "3. 'leq', 'L', or '=L=''  -- less than or equal to inequality \n"
                "4. 'nonbinding', 'N', or '=N='  -- nonbinding relationship \n"
                "5. 'cone', 'C', or '=C=' -- cone equation \n"
                "6. 'external', 'X', or '=X=' -- external equation \n"
                "7. 'boolean', 'B', or '=B=' -- boolean equation \n\n"
                f"User passed: `{typ}`"
            )

        # check to see if _symbol_type is being changed
        if getattr(self, "type", None) is not None:
            if self._type is not typ:
                self._requires_state_check = True

                self.container._requires_state_check = True
                self.container.modified = True

                # set the symbol type
                self._type = EQU_TYPE[typ]
                self.modified = True
        else:
            # set the symbol type
            self._type = EQU_TYPE[typ]
            self.modified = True
