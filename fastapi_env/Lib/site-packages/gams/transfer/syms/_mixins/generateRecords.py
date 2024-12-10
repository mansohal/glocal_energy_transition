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

import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype
from gams.transfer._internals import cartesian_product, choice_no_replace
from typing import Optional, Union, Callable


class GenerateRecordsBase:
    def generateRecords(self, density=None, seed=None):
        #
        # ARG: density
        if not isinstance(density, (int, float, list, type(None))):
            raise TypeError(
                "Argument 'density' must be type int, float, list or NoneType"
            )

        if density is None:
            density = 1.0

        if isinstance(density, list):
            if len(density) != self.dimension:
                raise ValueError(
                    f"Argument 'density' must be of length <symbol>.dimension ({len(density)} != {self.dimension})"
                )

            for dense in density:
                if not isinstance(dense, (int, float)):
                    raise TypeError(
                        "Argument 'density' must contain only type int or float"
                    )

                if not (dense >= 0 and dense <= 1):
                    raise ValueError(
                        "Argument 'density' must contain values on the interval [0,1]."
                    )

        # check if domain is "regular"
        if self.domain_type != "regular":
            raise Exception(
                "Cannot generate records unless the symbol has domain "
                "objects for all dimensions (i.e., <symbol>.domain_type == 'regular')"
            )

        # check all domain objects have records
        for symobj in self.domain:
            if symobj.records is None:
                raise Exception(
                    f"Symbol `{symobj.name}` was used as a domain, but it does not have records "
                    "-- cannot generate records unless all domain objects have records."
                )

        # if empty
        is_empty = False
        if isinstance(density, (int, float)):
            if density == 0:
                is_empty = True
        elif isinstance(density, list):
            if any(d == 0 for d in density):
                is_empty = True

        return density, is_empty

    def _set_empty(self):
        self.records = pd.DataFrame(
            columns=[list(range(self.dimension + len(self._attributes)))]
        )

        # set column names
        self.domain_labels = self.domain_names

        for x, symobj in enumerate(self.domain):
            self.records.isetitem(
                x, self.records.iloc[:, x].astype(CategoricalDtype([], ordered=True))
            )


class GenerateRecordsSetMixin(GenerateRecordsBase):
    def generateRecords(
        self,
        density: Optional[Union[int, float, list]] = None,
        seed: Optional[int] = None,
    ) -> None:
        """
        Convenience method to set standard pandas.DataFrame formatted records given domain set information. Will generate records with the Cartesian product of all domain sets

        Parameters
        ----------
        density : int | float | list, optional
            Takes any value on the interval [0,1]. If density is <1 then randomly selected records will be removed. `density` will accept a `list` of length `dimension` -- allows users to specify a density per symbol dimension, by default None
        seed : int, optional
            Random number state can be set with `seed` argument, by default None
        """
        # check & set
        density, is_empty = super().generateRecords(density, seed)

        if is_empty:
            super()._set_empty()

        # if not empty
        else:
            if isinstance(density, (int, float)):
                dtypes = []
                for n, symobj in enumerate(self.domain):
                    cats = symobj.getUELs(ignore_unused=True)
                    dtypes.append(CategoricalDtype(cats, ordered=True))

                codes = [np.arange(len(dtype.categories)) for dtype in dtypes]
                arr = cartesian_product(*tuple(codes))
                r, c = arr.shape
                idx = choice_no_replace(r, density * r, seed=seed)

                # set records
                self.records = pd.DataFrame(arr[idx, ...])

                # create categoricals from_codes
                for x, symobj in enumerate(self.domain):
                    self.records.isetitem(
                        x,
                        pd.Categorical.from_codes(
                            codes=self.records.iloc[:, x], dtype=dtypes[x]
                        ),
                    )

                # add element_text column
                self.records.insert(len(self.records.columns), "element_text", "")

                # set column names
                self.domain_labels = self.domain_names

                # remove unused categories
                self.removeUELs()

            elif isinstance(density, list):
                codes = []
                dtypes = []
                for n, (symobj, dense) in enumerate(zip(self.domain, density)):
                    cats = symobj.getUELs(ignore_unused=True)
                    dtypes.append(CategoricalDtype(cats, ordered=True))

                    codes.append(
                        choice_no_replace(len(cats), dense * len(cats), seed=seed)
                    )

                # set records
                self.records = pd.DataFrame(cartesian_product(*tuple(codes)))

                # create categoricals from_codes
                for x, symobj in enumerate(self.domain):
                    self.records.isetitem(
                        x,
                        pd.Categorical.from_codes(
                            codes=self.records.iloc[:, x], dtype=dtypes[x]
                        ),
                    )

                # add element_text column
                self.records.insert(len(self.records.columns), "element_text", "")

                # set column names
                self.domain_labels = self.domain_names

                # remove unused categories
                self.removeUELs()

            else:
                raise TypeError(
                    f"Encountered unsupported 'density' type: {type(density)} "
                )


class GenerateRecordsParameterMixin(GenerateRecordsBase):
    def generateRecords(
        self,
        density: Optional[Union[int, float, list]] = None,
        func: Optional[Callable] = None,
        seed: Optional[int] = None,
    ) -> None:
        """
        Convenience method to set standard pandas.DataFrame formatted records given domain set information. Will generate records with the Cartesian product of all domain sets.

        Parameters
        ----------
        density : int | float | list, optional
            Takes any value on the interval [0,1]. If density is <1 then randomly selected records will be removed. `density` will accept a `list` of length `dimension` -- allows users to specify a density per symbol dimension, by default None
        func : Callable, optional
            Functions to generate the records, by default None; numpy.random.uniform(0,1)
        seed : int, optional
            Random number state can be set with `seed` argument, by default None
        """
        # check & set
        density, is_empty = super().generateRecords(density, seed)

        #
        # ARG: func
        if not (callable(func) or func is None):
            raise TypeError("Argument 'func' must be a callable or None")

        # if empty
        if is_empty:
            super()._set_empty()

        # if not empty
        else:
            if isinstance(density, (int, float)):
                dtypes = []
                for n, symobj in enumerate(self.domain):
                    cats = symobj.getUELs(ignore_unused=True)
                    dtypes.append(CategoricalDtype(cats, ordered=True))

                codes = [np.arange(len(dtype.categories)) for dtype in dtypes]
                arr = cartesian_product(*tuple(codes))
                r, c = arr.shape
                idx = choice_no_replace(r, density * r, seed=seed)

                # set records
                self.records = pd.DataFrame(arr[idx, ...])

                # create categoricals from_codes
                for x, symobj in enumerate(self.domain):
                    self.records.isetitem(
                        x,
                        pd.Categorical.from_codes(
                            codes=self.records.iloc[:, x], dtype=dtypes[x]
                        ),
                    )

                # add value column
                try:
                    if func is None:
                        rng = np.random.default_rng(seed)
                        self.records["value"] = rng.uniform(
                            low=0.0, high=1.0, size=(len(self.records),)
                        )
                    else:
                        self.records["value"] = func(
                            seed=seed, size=(len(self.records),)
                        )
                        self.records["value"] = self.records["value"].astype(float)

                    # set column names
                    self.domain_labels = self.domain_names

                except Exception as err:
                    raise err

                # remove unused categories
                self.removeUELs()

            elif isinstance(density, list):
                codes = []
                dtypes = []
                for n, (symobj, dense) in enumerate(zip(self.domain, density)):
                    cats = symobj.getUELs(ignore_unused=True)
                    dtypes.append(CategoricalDtype(cats, ordered=True))

                    codes.append(
                        choice_no_replace(len(cats), dense * len(cats), seed=seed)
                    )

                # set records
                self.records = pd.DataFrame(cartesian_product(*tuple(codes)))

                # create categoricals from_codes
                for x, symobj in enumerate(self.domain):
                    self.records.isetitem(
                        x,
                        pd.Categorical.from_codes(
                            codes=self.records.iloc[:, x], dtype=dtypes[x]
                        ),
                    )

                # add value column
                try:
                    if func is None:
                        rng = np.random.default_rng(seed)
                        self.records["value"] = rng.uniform(
                            low=0.0, high=1.0, size=(len(self.records),)
                        )
                    else:
                        self.records["value"] = func(
                            seed=seed, size=(len(self.records),)
                        )
                        self.records["value"] = self.records["value"].astype(float)

                        # set column names
                        self.domain_labels = self.domain_names
                except Exception as err:
                    raise err

            else:
                raise TypeError(
                    f"Encountered unsupported 'density' type: {type(density)} "
                )

            # remove unused categories
            self.removeUELs()


class GenerateRecordsVariableMixin(GenerateRecordsBase):
    def generateRecords(
        self,
        density: Optional[Union[int, float, list]] = None,
        func: Optional[Callable] = None,
        seed: Optional[int] = None,
    ) -> None:
        """
        Convenience method to set standard pandas.DataFrame formatted records given domain set information. Will generate records with the Cartesian product of all domain sets.

        Parameters
        ----------
        density : int | float | list, optional
            Takes any value on the interval [0,1]. If density is <1 then randomly selected records will be removed. `density` will accept a `list` of length `dimension` -- allows users to specify a density per symbol dimension, by default None
        func : Callable, optional
            Functions to generate the records, by default None; numpy.random.uniform(0,1)
        seed : int, optional
            Random number state can be set with `seed` argument, by default None
        """
        # check & set
        density, is_empty = super().generateRecords(density, seed)

        #
        # ARG: func
        if not isinstance(func, (dict, type(None))):
            raise TypeError("Argument 'func' must be a dict or NoneType")

        if isinstance(func, dict):
            # check all keys in func dict
            if any(i not in self._attributes for i in func.keys()):
                raise Exception(
                    f"Unrecognized equation attribute detected in `func`. "
                    f"Attributes must be {self._attributes}, user passed "
                    f"dict keys: {list(func.keys())}."
                )

            # check that all func equation attributes are callable
            for i in func.keys():
                if not callable(func[i]):
                    raise TypeError(
                        f"Object supplied to `func` argument (`{i}`) must be callable -- received {type(func[i])}"
                    )

        # if empty
        if is_empty:
            super()._set_empty()

        # if not empty
        else:
            if isinstance(density, (int, float)):
                dtypes = []
                for n, symobj in enumerate(self.domain):
                    cats = symobj.getUELs(ignore_unused=True)
                    dtypes.append(CategoricalDtype(cats, ordered=True))

                codes = [np.arange(len(dtype.categories)) for dtype in dtypes]
                arr = cartesian_product(*tuple(codes))
                r, c = arr.shape
                idx = choice_no_replace(r, density * r, seed=seed)

                # set records
                self.records = pd.DataFrame(arr[idx, ...])

                # create categoricals from_codes
                for x, symobj in enumerate(self.domain):
                    self.records.isetitem(
                        x,
                        pd.Categorical.from_codes(
                            codes=self.records.iloc[:, x], dtype=dtypes[x]
                        ),
                    )

                # add attribute columns
                try:
                    if func is None:
                        rng = np.random.default_rng(seed)
                        self.records["level"] = rng.uniform(
                            low=0.0, high=1.0, size=(len(self.records),)
                        )

                        for i in self._attributes:
                            if i != "level":
                                self.records[i] = self.default_records[i]

                    else:
                        for i in self._attributes:
                            if i in func.keys():
                                self.records[i] = func[i](
                                    seed=seed, size=(len(self.records),)
                                )
                                self.records[i] = self.records[i].astype(float)
                            else:
                                self.records[i] = self.default_records[i]

                    # set column names
                    self.domain_labels = self.domain_names

                except Exception as err:
                    raise err

                # remove unused categories
                self.removeUELs()

            elif isinstance(density, list):
                codes = []
                dtypes = []
                for n, (symobj, dense) in enumerate(zip(self.domain, density)):
                    cats = symobj.getUELs(ignore_unused=True)
                    dtypes.append(CategoricalDtype(cats, ordered=True))

                    codes.append(
                        choice_no_replace(len(cats), dense * len(cats), seed=seed)
                    )

                # set records
                self.records = pd.DataFrame(cartesian_product(*tuple(codes)))

                # create categoricals from_codes
                for x, symobj in enumerate(self.domain):
                    self.records.isetitem(
                        x,
                        pd.Categorical.from_codes(
                            codes=self.records.iloc[:, x], dtype=dtypes[x]
                        ),
                    )

                # add attribute columns
                try:
                    if func is None:
                        rng = np.random.default_rng(seed)
                        self.records["level"] = rng.uniform(
                            low=0.0, high=1.0, size=(len(self.records),)
                        )

                        for i in self._attributes:
                            if i != "level":
                                self.records[i] = self.default_records[i]

                    else:
                        for i in self._attributes:
                            if i in func.keys():
                                self.records[i] = func[i](
                                    seed=seed, size=(len(self.records),)
                                )
                                self.records[i] = self.records[i].astype(float)
                            else:
                                self.records[i] = self.default_records[i]

                    # set column names
                    self.domain_labels = self.domain_names

                except Exception as err:
                    raise err

                # remove unused categories
                self.removeUELs()

            else:
                raise TypeError(
                    f"Encountered unsupported 'density' type: {type(density)} "
                )


class GenerateRecordsEquationMixin(GenerateRecordsVariableMixin): ...
