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

from gams.transfer._internals import DICT_FORMAT, DictFormat


def _toDict_orient_chk(orient):
    if orient is None:
        orient = "natural"

    if orient.casefold() not in DICT_FORMAT.keys():
        raise ValueError(
            f"Argument 'orient' expects one of the following (mixed-case OK): {list(DICT_FORMAT.keys())}"
        )

    return DICT_FORMAT[orient.casefold()]


def toDictParameter(symbol, orient=None):
    # check and/or set orient
    orient = _toDict_orient_chk(orient)

    if symbol.is_scalar:
        raise TypeError(
            f"Symbol `{symbol.name}` is a scalar and cannot be converted into a dict."
        )

    if symbol.records is not None:
        if orient is DictFormat.NATURAL:
            if symbol.dimension == 1:
                return dict(zip(symbol.records.iloc[:, 0], symbol.records.iloc[:, -1]))

            else:
                doms = zip(
                    *[symbol.records.iloc[:, i] for i in range(symbol.dimension)]
                )
                vals = symbol.records[symbol.records.columns[-1]]

                return dict(zip(doms, vals))

        if orient is DictFormat.COLUMNS:
            return symbol.records.to_dict()


def toDictVariableEquation(symbol, columns=None, orient=None):
    # check and/or set orient
    orient = _toDict_orient_chk(orient)

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

    if symbol.is_scalar:
        raise TypeError(
            f"Symbol `{symbol.name}` is a scalar and cannot be converted into a dict."
        )

    if symbol.records is not None:
        if orient is DictFormat.NATURAL:
            if symbol.dimension == 1:
                doms = symbol.records.iloc[:, 0]
            else:
                doms = zip(
                    *[symbol.records.iloc[:, i] for i in range(symbol.dimension)]
                )

            if len(columns) == 1:
                return dict(zip(doms, symbol.records[columns[0]]))
            else:
                vals = symbol.records[columns].to_dict("records")

                return dict(zip(doms, vals))

        if orient is DictFormat.COLUMNS:
            return symbol.records[symbol.domain_labels + columns].to_dict()
