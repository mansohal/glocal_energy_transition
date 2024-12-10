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


def toValueParameter(symbol):
    if not symbol.is_scalar:
        raise TypeError(
            "Cannot extract value data for non-scalar symbols "
            f"(symbol dimension is {symbol.dimension})"
        )

    if symbol.records is not None:
        return symbol.records["value"][0]


def toValueVariableEquation(symbol, column=None):
    if not symbol.is_scalar:
        raise TypeError(
            "Cannot extract value data for non-scalar symbols "
            f"(symbol dimension is {symbol.dimension})"
        )

    # checks
    if column is None:
        column = "level"

    if not isinstance(column, str):
        raise TypeError(
            f"Argument 'column' must be type str. User passed {type(column)}."
        )

    if column not in symbol._attributes:
        raise TypeError(
            f"Argument 'column' must be one of the following: {symbol._attributes}"
        )

    if symbol.records is not None:
        return symbol.records[column][0]
