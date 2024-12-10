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


def toListSet(symbol, include_element_text=False):
    if not isinstance(include_element_text, bool):
        raise TypeError("Argument 'include_element_text' must be type bool")

    if symbol.records is not None:
        if include_element_text:
            return symbol.records.set_index(
                symbol.records.columns.to_list()
            ).index.to_list()
        else:
            return symbol.records.set_index(
                symbol.records.columns.to_list()[: symbol.dimension]
            ).index.to_list()


def toListParameter(symbol):
    if symbol.records is not None:
        if symbol.is_scalar:
            return list(symbol.records.iloc[:, 0])
        else:
            return list(
                zip(
                    *[
                        symbol.records.iloc[:, x]
                        for x in range(len(symbol.records.columns))
                    ]
                )
            )


def toListVariableEquation(symbol, columns=None):
    # ARG: columns
    # set defaults
    if columns is None:
        columns = "level"

    # checks
    if not isinstance(columns, (str, list)):
        raise TypeError(
            f"Argument 'columns' must be type str or list. User passed {type(columns)}."
        )

    if isinstance(columns, str):
        columns = [columns]

    if any(not isinstance(i, str) for i in columns):
        raise TypeError(f"Argument 'columns' must contain only type str.")

    if any(i not in symbol._attributes for i in columns):
        raise TypeError(
            f"Argument 'columns' must be a subset of the following: {symbol._attributes}"
        )

    if symbol.records is not None:
        return symbol.records.set_index(
            [i for i in symbol.domain_labels + columns]
        ).index.to_list()
