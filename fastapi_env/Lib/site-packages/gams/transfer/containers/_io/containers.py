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
import gams.transfer._abcs as abcs
from gams.transfer.syms import (
    Set,
    Parameter,
    Variable,
    Equation,
    Alias,
    UniverseAlias,
)
from typing import Union, List


def read(
    container: "abcs.ABCContainer",
    load_from: "abcs.ABCContainer",
    symbols: Union[List[str], None],
    records: bool,
):
    """
    Read symbols and associated data from a source Container into a target Container.

    Parameters
    ----------
    container : Container
        The target Container where the symbols and data will be read into.
    load_from : Container
        The source Container from which symbols and data will be read.
    symbols : List[str] | None
        A list of symbol names to read from the source Container. If not provided, all symbols in the source Container
        will be read.
    records : bool

    Raises
    ------
    ValueError
        If a specified symbol in the 'symbols' list does not exist in the source Container.
    Exception
        If there are conflicts or issues with the symbol names, object types, or symbol domains during the read
        operation.
    """
    if symbols is None:
        read_symbols = list(load_from.data.keys())
    else:
        for i in symbols:
            if i not in load_from:
                raise ValueError(
                    f"User specified to read symbol `{i}`, "
                    "but it does not exist in the source Container."
                )

        read_symbols = symbols

    # checks
    for symname, symobj in zip(read_symbols, load_from.getSymbols(read_symbols)):
        # check to make sure that all read_symbols are valid
        if isinstance(load_from, abcs.ABCContainer):
            if symobj.isValid() is False:
                raise Exception(
                    f"Cannot read symbol `{symname}` because it is invalid, use "
                    "`<symbol>.isValid(verbose=True)` "
                    "method to debug symbol state."
                )

        # check if there are any duplicate symbols in the container
        if symname in container:
            raise Exception(
                f"Attempting to create a new symbol (through a read operation) named `{symname}` "
                "but an object with this name already exists in the Container. "
                "Symbol replacement is only possible if the existing symbol is "
                "first removed from the Container with the `<container>.removeSymbols()` method."
            )

    # read in symbols
    cf_read_symbols = list(map(str.casefold, read_symbols))
    link_domains = []
    for symname, symobj in load_from.data.items():
        if symname.casefold() in cf_read_symbols:
            # if a symbol has any domain references we would want to keep those
            if any(
                isinstance(domobj, abcs.AnyContainerDomainSymbol)
                for domobj in symobj.domain
            ):
                link_domains.append((symname, symobj.domain_names))

            if isinstance(symobj, abcs.ABCSet):
                Set(
                    container,
                    symname,
                    domain=symobj.domain_names,
                    is_singleton=symobj.is_singleton,
                    records=copy.deepcopy(symobj.records),
                    description=symobj.description,
                )
            elif isinstance(symobj, abcs.ABCParameter):
                Parameter(
                    container,
                    symname,
                    domain=symobj.domain_names,
                    records=copy.deepcopy(symobj.records),
                    description=symobj.description,
                )
            elif isinstance(symobj, abcs.ABCVariable):
                Variable(
                    container,
                    symname,
                    type=symobj.type,
                    domain=symobj.domain_names,
                    records=copy.deepcopy(symobj.records),
                    description=symobj.description,
                )

            elif isinstance(symobj, abcs.ABCEquation):
                Equation(
                    container,
                    symname,
                    type=symobj.type,
                    domain=symobj.domain_names,
                    records=copy.deepcopy(symobj.records),
                    description=symobj.description,
                )

            elif isinstance(symobj, abcs.ABCAlias):
                Alias(
                    container,
                    symname,
                    container.data[symobj.alias_with.name],
                )
            elif isinstance(symobj, abcs.ABCUniverseAlias):
                UniverseAlias(container, symname)

    # link domain objects
    for symname, domain in link_domains:
        domain = list(map(str.casefold, domain))
        for n, i in enumerate(domain):
            if i in container and i in cf_read_symbols:
                domain[n] = container[i]

        container[symname].domain = domain
