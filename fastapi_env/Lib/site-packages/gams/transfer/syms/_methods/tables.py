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

AXES = ["index", "columns"]


def _get_implied_dimension_from_axes(records):
    return sum([axis.nlevels for axis in records.axes])


def _assert_axes_no_nans(records):
    for axis_name, axis in zip(AXES, records.axes):
        if isinstance(axis, pd.MultiIndex):
            for n in range(axis.nlevels):
                if axis.get_level_values(n).hasnans:
                    raise Exception(
                        "Tabular 'records' cannot have missing index information "
                        f"(i.e., NaNs detected in `records.{axis_name}.get_level_values({n})`)"
                    )
        else:
            if axis.hasnans:
                raise Exception(
                    "Tabular 'records' cannot have missing index information "
                    f"(i.e., NaNs detected in `records.{axis_name}`)"
                )


def _flatten_and_convert(records):
    AXES = ["index", "columns"]
    drop_needed = False
    for axis_name, axis in zip(AXES, records.axes):
        idx = pd.DataFrame(columns=list(range(axis.nlevels)))

        # go through axis
        for n in range(axis.nlevels):
            level = axis.levels[n] if hasattr(axis, "levels") else axis

            # factorize
            # preserve order of appearance, not lexicographical order + str/rstrip
            codes, cats = pd.Series(
                map(str.rstrip, map(str, axis.get_level_values(n)))
            ).factorize()

            # create categorical
            categorical = pd.Categorical.from_codes(
                codes, categories=cats, ordered=True
            )

            # preserve user order if CategoricalDtype
            if isinstance(level.dtype, pd.CategoricalDtype):
                categorical = categorical.reorder_categories(
                    dict.fromkeys(map(str.rstrip, level.categories)),
                    ordered=True,
                )

            # set
            idx.isetitem(n, categorical)

        # TODO: need a workaround here to avoid an error with pandas stack
        if axis_name == "columns":
            if idx.set_index(list(idx.columns)).index.has_duplicates:
                drop_needed = True
                idx["__ai"] = range(len(idx))

        # create categorical index and set on records
        setattr(records, axis_name, idx.set_index(list(idx.columns)).index)

        # remove names
        getattr(records, axis_name).names = [None] * getattr(records, axis_name).nlevels

    if isinstance(records, pd.DataFrame):
        major, minor, *_ = pd.__version__.split(".")
        major, minor = (int(major), int(minor))

        # TODO: remove in future... allows support for pandas < 2.1.0
        if (major, minor) >= (2, 2):
            to_drop = (records.index.nlevels - 1) + (records.columns.nlevels)
            records = records.stack(
                list(range(records.columns.nlevels)),
                future_stack=True,
            ).reset_index(drop=False)
        else:
            to_drop = (records.index.nlevels - 1) + (records.columns.nlevels)
            records = records.stack(
                list(range(records.columns.nlevels)), dropna=False
            ).reset_index(drop=False)

        if drop_needed:
            records.drop(columns=records.columns[to_drop], inplace=True)
    else:
        records = records.reset_index(drop=False)

    return records
