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

from gams.transfer._abcs import (
    ABCSet,
    ABCAlias,
    ABCParameter,
    ABCVariable,
    ABCEquation,
    AnyContainerDomainSymbol,
)
from typing import List, Union


class DomainViolation:
    def __init__(self, symbol, dimension, domain, violations):
        self.symbol = symbol
        self.dimension = dimension
        self.domain = domain
        self.violations = violations

    def __repr__(self):
        return f"<DomainViolation ({hex(id(self))})>"

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(
        self,
        symbol: Union[
            "ABCSet", "ABCAlias", "ABCParameter", "ABCVariable", "ABCEquation"
        ],
    ) -> None:
        if not isinstance(
            symbol, (ABCSet, ABCAlias, ABCParameter, ABCVariable, ABCEquation)
        ):
            raise TypeError(
                "Argument 'symbol' expects objects of the _Symbol parent "
                "class (i.e., a Set, Alias, Parameter, Variable, Equation)"
            )

        self._symbol = symbol

    @property
    def dimension(self):
        return self._dimension

    @dimension.setter
    def dimension(self, dimension: int) -> None:
        if not isinstance(dimension, int):
            raise TypeError("Argument 'dimension' must be of type int")

        self._dimension = dimension

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, domain: "AnyContainerDomainSymbol") -> None:
        if not isinstance(domain, AnyContainerDomainSymbol):
            raise TypeError(
                "Argument 'symbol' expects Set, Alias, or UniverseAlias objects"
            )
        self._domain = domain

    @property
    def violations(self):
        return self._violations

    @violations.setter
    def violations(self, violations: List[str]) -> None:
        if not isinstance(violations, list):
            raise TypeError("Argument 'violations' must be type list")

        if any(not isinstance(i, str) for i in violations):
            raise TypeError("Argument 'violations' must only contain type str")

        self._violations = violations
