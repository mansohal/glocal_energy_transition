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
import random
import numpy as np
import pandas as pd
import gams.transfer._abcs as abcs
from typing import Sequence, Tuple, Union, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gams.transfer.syms import Set, Parameter, Variable, Equation


def check_all_same(iterable1: Sequence, iterable2: Sequence) -> bool:
    """
    Check if two sequences have the same elements in the same order.

    Parameters
    ----------
    iterable1 : Sequence
        The first sequence to compare.

    iterable2 : Sequence
        The second sequence to compare.

    Returns
    -------
    bool
        Returns True if both sequences have the same elements in the same order; otherwise, False.
    """
    if len(iterable1) != len(iterable2):
        return False

    all_same = True
    for elem1, elem2 in zip(iterable1, iterable2):
        if elem1 is not elem2:
            return False
    return all_same


def get_keys_and_values(
    symobj: Union["Set", "Parameter", "Variable", "Equation"], mode: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gets the keys and values of a specific symbol.

    Parameters
    ----------
    symobj : Set | Parameter | Variable | Equation
        The symbol to explore.
    mode : str
        The mode of keys and values; string or category.

    Returns
    -------
    Tuple[ndarray, ndarray]
        The tuple includes the symbol's keys and values.

    Raises
    ------
    ValueError
        If the given mode is niether 'string' nor 'category'.
    """
    if symobj.records is None:
        if isinstance(symobj, abcs.ABCSet):
            arrkeys = np.full(
                (0, symobj.dimension), "", dtype=dtype_keys
            )  # dtype_keys is not defined
            arrvals = np.full((0, 1), "", dtype=object)
            return (arrkeys, arrvals)
        if isinstance(symobj, abcs.ABCParameter):
            arrkeys = np.full(
                (0, symobj.dimension), "", dtype=dtype_keys
            )  # dtype_keys is not defined
            arrvals = np.full((0, len(symobj._attributes)), "", dtype=np.float64)
            return (arrkeys, arrvals)
        if isinstance(symobj, (abcs.ABCVariable, abcs.ABCEquation)):
            arrkeys = np.full(
                (0, symobj.dimension), "", dtype=dtype_keys
            )  # dtype_keys is not defined
            arrvals = np.full((0, len(symobj._attributes)), "", dtype=np.float64)
            return (arrkeys, arrvals)

    else:
        #
        #
        # get keys array
        if mode == "string":
            nrecs = symobj.number_records
            if symobj.dimension == 0:
                arrkeys = np.array([[]], dtype=object)
            elif symobj.dimension == 1:
                arrkeys = np.empty(nrecs, dtype=object)
                arrkeys[:nrecs] = symobj.records[symobj.records.columns[0]]
                arrkeys = arrkeys.reshape((nrecs, 1), order="F")
            else:
                arrkeys = np.empty(symobj.dimension * nrecs, dtype=object)
                for i in range(symobj.dimension):
                    idx_start = i * nrecs
                    idx_end = i * nrecs + nrecs
                    arrkeys[idx_start:idx_end] = symobj.records[
                        symobj.records.columns[i]
                    ]

                arrkeys = arrkeys.reshape((nrecs, symobj.dimension), order="F")

        elif mode == "category":
            nrecs = symobj.number_records
            if symobj.dimension == 0:
                arrkeys = np.array([[]], dtype=int)
            elif symobj.dimension == 1:
                arrkeys = np.empty(nrecs, dtype=int)
                arrkeys[:nrecs] = symobj.records[symobj.records.columns[0]].cat.codes
                arrkeys = arrkeys.reshape((nrecs, 1), order="F")
            else:
                arrkeys = np.empty(symobj.dimension * nrecs, dtype=int)
                for i in range(symobj.dimension):
                    idx_start = i * nrecs
                    idx_end = i * nrecs + nrecs
                    arrkeys[idx_start:idx_end] = symobj.records[
                        symobj.records.columns[i]
                    ].cat.codes

                arrkeys = arrkeys.reshape((nrecs, symobj.dimension), order="F")
        else:
            raise ValueError("Unrecognized write 'mode'.")
        #
        #
        # get values array
        if symobj.dimension == 0:
            arrvals = symobj.records.to_numpy()
        else:
            if isinstance(symobj, (abcs.ABCSet, abcs.ABCParameter)):
                arrvals = (
                    symobj.records[symobj.records.columns[-1]]
                    .to_numpy()
                    .reshape((-1, 1))
                )
            else:
                arrvals = np.empty(len(symobj._attributes) * nrecs, dtype=np.float64)
                for i in range(len(symobj._attributes)):
                    idx_start = i * nrecs
                    idx_end = i * nrecs + nrecs
                    arrvals[idx_start:idx_end] = symobj.records[
                        symobj.records.columns[i + symobj.dimension]
                    ].to_numpy()

                arrvals = arrvals.reshape((nrecs, len(symobj._attributes)), order="F")

        return (arrkeys, arrvals)


def convert_to_categoricals_str(
    arrkeys: np.ndarray, arrvals: np.ndarray, all_uels: Sequence
) -> pd.DataFrame:
    """
    This function takes two lists, `arrkeys` and `arrvals`, and converts them into a pandas
    DataFrame.

    Parameters
    ----------
    arrkeys : ndarray
        An array of keys (e.g., labels or domain values).

    arrvals : ndarray
        An array of values corresponding to the keys.

    all_uels : Sequence
        A sequence of all unique elements (categories) that should be used to define
        the categorical data.

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame with categorical columns based on `arrkeys` and `arrvals`.

    Notes
    -----
    - This function assumes that the lengths of `arrkeys` and `arrvals` are compatible.
    """
    has_domains = arrkeys.size > 0
    has_values = arrvals.size > 0

    dfs = []
    if has_domains:
        dfs.append(pd.DataFrame(arrkeys))

    if has_values:
        dfs.append(pd.DataFrame(arrvals))

    if has_domains and has_values:
        df = pd.concat(dfs, axis=1, copy=False)
        df.columns = pd.RangeIndex(start=0, stop=len(df.columns))
    elif has_domains or has_values:
        df = dfs[0]
        df.columns = pd.RangeIndex(start=0, stop=len(df.columns))
    else:
        df = None

    if has_domains:
        rk, ck = arrkeys.shape
        for i in range(ck):
            dtype = pd.CategoricalDtype(categories=all_uels, ordered=True)
            df.isetitem(
                i, pd.Categorical(values=df[i], dtype=dtype).remove_unused_categories()
            )

    return df


def convert_to_categoricals_cat(
    arrkeys: np.ndarray, arrvals: np.ndarray, unique_uels: Sequence
) -> pd.DataFrame:
    has_domains = arrkeys.size > 0
    has_values = arrvals.size > 0

    dfs = []
    if has_domains:
        dfs.append(pd.DataFrame(arrkeys))

    if has_values:
        dfs.append(pd.DataFrame(arrvals))

    if has_domains and has_values:
        df = pd.concat(dfs, axis=1, copy=False)
        df.columns = pd.RangeIndex(start=0, stop=len(df.columns))
    elif has_domains or has_values:
        df = dfs[0]
        df.columns = pd.RangeIndex(start=0, stop=len(df.columns))
    else:
        df = None

    if has_domains:
        _, ck = arrkeys.shape
        for i in range(ck):
            dtype = pd.CategoricalDtype(categories=unique_uels[i], ordered=True)
            df.isetitem(i, pd.Categorical.from_codes(codes=df[i], dtype=dtype))

    return df


def generate_unique_labels(labels: Union[list, str]) -> List[str]:
    """
    Generate unique labels from a list of labels.

    Parameters
    ----------
    labels : list | str
        A list of labels to be processed. This can be a single label or a list of labels.

    Returns
    -------
    List[str]
        A list of labels with uniqueness enforced. If the input list contains duplicates, this
        function appends numeric suffixes to make the labels unique. If the input is not a list,
        it is converted to a single-element list.
    """
    if not isinstance(labels, list):
        labels = [labels]

    # default domain labels
    labels = [i if i != "*" else "uni" for i in labels]

    # make unique
    is_unique = False
    if len(labels) == len(set(labels)):
        is_unique = True

    if not is_unique:
        labels = [f"{i}_{n}" for n, i in enumerate(labels)]

    return labels


def cartesian_product(*arrays: Tuple[np.ndarray]) -> np.ndarray:
    """
    Calculate the Cartesian product of multiple input arrays.

    Given multiple input arrays, this function computes the Cartesian product of these arrays.
    The Cartesian product is an array containing all possible combinations of elements from
    the input arrays, where each element in the result is a tuple representing one combination.

    Parameters
    ----------
    *arrays : Tuple[ndarray]
        Multiple input arrays for which the Cartesian product is calculated.

    Returns
    -------
    ndarray
        A NumPy array containing the Cartesian product of the input arrays. Each row
        represents a unique combination, and the columns represent the elements from the
        input arrays.

    Notes
    -----
    - The input arrays should be of compatible data types.
    - The number of input arrays and their shapes may vary, and the function works for any
      number of input arrays.

    Examples
    -------_
    >>> import numpy as np
    >>> arr1 = np.array([1, 2])
    >>> arr2 = np.array(['A', 'B'])
    >>> arr3 = np.array([0.1, 0.2])
    >>> result = cartesian_product(arr1, arr2, arr3)
    >>> print(result)
    array([[1, 'A', 0.1],
           [1, 'A', 0.2],
           [1, 'B', 0.1],
           [1, 'B', 0.2],
           [2, 'A', 0.1],
           [2, 'A', 0.2],
           [2, 'B', 0.1],
           [2, 'B', 0.2]], dtype=object)

    """

    la = len(arrays)
    dtype = np.result_type(*arrays)
    arr = np.empty((la, *map(len, arrays)), dtype=dtype)
    idx = slice(None), *itertools.repeat(None, la)
    for i, a in enumerate(arrays):
        arr[i, ...] = a[idx[: la - i]]

    return arr.reshape(la, -1).T


def choice_no_replace(
    choose_from: int,
    n_choose: int,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Randomly select 'n_choose' unique items from a pool of 'choose_from' items without replacement.

    This function allows you to randomly choose a specified number of unique items from a pool of items
    defined by 'choose_from'. It ensures that the selected items are unique, meaning each item is chosen
    only once.

    Parameters
    ----------
    choose_from : int
        The total number of items to choose from.

    n_choose : int
        The number of items to select from the pool.

    seed : int, optional
        An optional seed for the random number generator. If provided, it should be an integer or None.
        If 'seed' is None, the random selection will not be reproducible.

    Returns
    -------
    ndarray
        An array containing the selected items. The array will have a length of 'n_choose', and the
        items will be in random order.

    Raises
    ------
    TypeError
        If 'seed' is not an integer or None.

    Exception
        If the 'density' of selection is out of bounds, which must be in the interval [0, 1].

    Notes
    -----
    - For high-density selections (density > 0.08), NumPy is used for better performance.
    - For low-density selections (density <= 0.08), the built-in 'random' module is used for speed.

    Examples
    --------
    >>> choice_no_replace(100, 10, seed=42)
    array([8, 9, 19, 41, 60, 68, 71, 82, 94, 96])
    """

    if not isinstance(seed, (int, type(None))):
        raise TypeError("Argument 'seed' must be type int or NoneType")

    if not isinstance(choose_from, int):
        choose_from = int(choose_from)

    if not isinstance(n_choose, int):
        n_choose = int(n_choose)

    density = n_choose / choose_from

    try:
        if density == 1:
            return np.arange(choose_from, dtype=int)

        # numpy is faster as density grows
        if 0.08 < density < 1:
            rng = np.random.default_rng(seed)
            idx = rng.choice(
                np.arange(choose_from, dtype=int), replace=False, size=(n_choose,)
            )

        # random.shuffle is much much faster at low density
        elif density <= 0.08:
            random.seed(seed)
            idx = np.array(random.sample(range(choose_from), n_choose), dtype=int)
        else:
            raise Exception(
                "Argument 'density' is out of bounds, must be on the interval [0,1]."
            )

        return np.sort(idx)

    except Exception as err:
        raise err
