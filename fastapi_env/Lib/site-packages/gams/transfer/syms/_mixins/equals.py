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
import numpy as np
from gams.transfer._abcs import ABCAlias, AnyContainerSymbol
from gams.transfer._internals import SpecialValues
import typing
from typing import Union, Optional

if typing.TYPE_CHECKING:
    from gams.transfer.syms.container_syms._set import Set
    from gams.transfer.syms.container_syms._alias import Alias
    from gams.transfer.syms.container_syms._parameter import Parameter
    from gams.transfer.syms.container_syms._variable import Variable


class EqualsBase:
    @typing.no_type_check
    def equals(self, other, check_uels, check_meta_data, verbose):
        #
        # ARG: self
        if not self.isValid():
            raise Exception(
                f"Cannot compare objects because `{self.name}` is not a valid symbol object"
                "Use `<symbol>.isValid(verbose=True)` to debug further."
            )

        #
        # ARG: other
        if not isinstance(other, AnyContainerSymbol):
            raise TypeError("Argument 'other' must be a GAMS Symbol object")

        if not other.isValid():
            raise Exception(
                f"Cannot compare objects because `{other.name}` is not a valid symbol object"
                "Use `<symbol>.isValid(verbose=True)` to debug further."
            )

        # adjustments
        if isinstance(other, ABCAlias):
            other = other.alias_with

        #
        # ARG: self & other
        if not isinstance(self, type(other)):
            raise TypeError(
                f"Symbol are not of the same type (`{type(self)}` != `{type(other)}`)"
            )

        # test for equal variable and equation types
        if getattr(self, "type", None) != getattr(other, "type", None):
            raise Exception(
                f"Symbol types do not match (`{self.type}` != `{other.type}`)"
            )

        #
        # ARG: check_uels
        if not isinstance(check_uels, bool):
            raise TypeError("Argument 'check_uels' must be type bool")

        #
        # ARG: check_meta_data
        if not isinstance(check_meta_data, bool):
            raise TypeError("Argument 'check_meta_data' must be type bool")

        #
        # ARG: verbose
        if not isinstance(verbose, bool):
            raise TypeError("Argument 'verbose' must be type bool")

        return other

    def _assert_symbol_attributes(
        self,
        other,
        check_uels,
        check_meta_data,
    ):
        #
        # Mandatory checks
        if self.dimension != other.dimension:
            raise Exception(
                f"Symbol dimensions do not match (`{self.dimension}` != `{other.dimension}`)"
            )

        if self.domain_type != other.domain_type:
            raise Exception(
                f"Symbol domain_types do not match (`{self.domain_type}` != `{other.domain_type}`)"
            )

        if self.records is not None and other.records is not None:
            if self.number_records != other.number_records:
                raise Exception(
                    "Symbols do not have the same number of records "
                    f"(`{self.number_records}` != `{other.number_records}`)"
                )

        if not isinstance(self.records, type(other.records)):
            raise Exception(
                f"Symbol records type do not match (`{type(self.records)}` != `{type(other.records)}`)"
            )

        # check domains even if symbols are in different containers
        different_containers = True if self.container is not other.container else False
        for n, (selfdom, otherdom) in enumerate(zip(self.domain, other.domain)):
            if type(selfdom) is not type(otherdom):
                raise Exception(
                    f"Domain symbols in dimension {n} (zero-indexed) are not the same type (i.e., '{selfdom.name}' "
                    f"is {type(selfdom)} does not match '{otherdom.name}' which is {type(otherdom)})"
                )

            if not different_containers:
                if selfdom is not otherdom:
                    raise Exception(
                        f"Domain symbols in dimension {n} (zero-indexed) are not the same object (i.e., '{selfdom.name}' is not '{otherdom.name}')"
                    )
            else:
                if not isinstance(selfdom, str):
                    if selfdom.name != otherdom.name:
                        raise Exception(
                            f"Domain symbols in dimension {n} (zero-indexed) do not have the same name (i.e., '{selfdom.name}' != '{otherdom.name}')"
                        )

                    try:
                        selfdom.equals(otherdom, verbose=True)
                    except Exception as err:
                        raise Exception(
                            f"Domain symbols '{selfdom.name}' are not equal . Reason: {err}"
                        ) from err

        #
        # Check metadata (optional)
        if check_meta_data:
            if self.name != other.name:
                raise Exception(
                    f"Symbol names do not match (`{self.name}` != `{other.name}`)"
                )

            if self.description != other.description:
                raise Exception(
                    f"Symbol descriptions do not match (`{self.description}` != `{other.description}`)"
                )

        # Check UELs (optional)
        if check_uels:
            if self.records is not None and other.records is not None:
                left_uels = self.getUELs()
                right_uels = other.getUELs()

                if left_uels != right_uels:
                    raise Exception(
                        "Symbol UEL ordering does not match \n\n"
                        f"[self]: {left_uels} \n"
                        f"[other]: {right_uels} \n"
                    )

    def _merge_records(self, other):
        merged = pd.DataFrame()
        if self.records is not None and other.records is not None:
            if not self.records.empty and not other.records.empty:
                merged = self.records.merge(
                    other.records,
                    how="outer",
                    left_on=self.domain_labels,
                    right_on=other.domain_labels,
                    indicator=True,
                )

        return merged

    def _assert_scalar_values(self, other, columns, rtol, atol):
        for attr in columns:
            for svlabel, SV in zip(
                ["EPS", "NA", "UNDEF"],
                [
                    SpecialValues.isEps,
                    SpecialValues.isNA,
                    SpecialValues.isUndef,
                ],
            ):
                self_is_special = SV(self.records[attr])
                other_is_special = SV(other.records[attr])

                if self_is_special != other_is_special:
                    raise Exception(
                        f"Symbol records with `{svlabel}` special values "
                        f"do not match in the `{attr}` column."
                    )

            if self_is_special == False and other_is_special == False:
                if not np.isclose(
                    self.records[attr],
                    other.records[attr],
                    rtol=rtol,
                    atol=atol,
                ):
                    raise Exception(
                        f"Symbol records contain numeric difference in the `{attr}` attribute "
                        f"that are outside the specified tolerances (rtol={rtol}, atol={atol})"
                    )

    @typing.no_type_check
    def _assert_symbol_domains(self, merged):
        if set(merged["_merge"]) != {"both"}:
            self_only_recs = merged[merged["_merge"].isin({"left_only"})].head()
            other_only_recs = merged[merged["_merge"].isin({"right_only"})].head()

            if self_only_recs.empty:
                self_only_recs = "All matched OK"
            else:
                self_only_recs = list(
                    self_only_recs[self_only_recs.columns[: self.dimension]].itertuples(
                        index=False, name=None
                    )
                )

            if other_only_recs.empty:
                other_only_recs = "All matched OK"
            else:
                other_only_recs = list(
                    other_only_recs[
                        other_only_recs.columns[: other.dimension]
                    ].itertuples(index=False, name=None)
                )

            raise Exception(
                "Symbol records do not match. First five unmatched domains: \n\n"
                f"left_only :  {self_only_recs} \n"
                f"right_only:  {other_only_recs} \n"
            )


class EqualsSetMixin(EqualsBase):
    @typing.no_type_check
    def equals(
        self,
        other: Union["Set", "Alias"],
        check_uels: bool = True,
        check_element_text: bool = True,
        check_meta_data: bool = True,
        verbose: bool = False,
    ) -> bool:
        """
        Used to compare the symbol to another symbol

        Parameters
        ----------
        other : Set | Alias
            Other Symbol to compare with
        check_uels : bool, optional
            If True, check both used and unused UELs and confirm same order, otherwise only check used UELs in data and do not check UEL order, by default True
        check_element_text : bool, optional
            If True, check that all set elements have the same descriptive element text, otherwise skip, by default True
        check_meta_data : bool, optional
            If True, check that symbol name and description are the same, otherwise skip, by default True
        verbose : bool, optional
            If True, will return an exception from the asserter describing the nature of the difference, by default False

        Returns
        -------
        bool
            True if symbols are equal, False otherwise
        """

        # check & set
        other = super().equals(other, check_uels, check_meta_data, verbose)

        # check is_singleton
        if self.is_singleton != other.is_singleton:
            raise Exception("Symbols do not have matching 'is_singleton' state")

        # extension to check check_element_text
        # ARG: check_element_text
        if not isinstance(check_element_text, bool):
            raise TypeError("Argument 'check_element_text' must be type bool")

        try:
            # check symbol attributes (not records)
            super()._assert_symbol_attributes(other, check_uels, check_meta_data)

            # merge records
            merged = super()._merge_records(other)

            # check symbol domain records
            self._assert_symbol_domains(merged, check_element_text)

            return True
        except Exception as err:
            if verbose:
                raise err
            else:
                return False

    @typing.no_type_check
    def _assert_symbol_domains(self, merged, check_element_text):
        if not merged.empty:
            # check domains
            super()._assert_symbol_domains(merged)

            # extension to check element text
            if check_element_text:
                merged["_element_text"] = (
                    merged["element_text_x"] != merged["element_text_y"]
                )

                recs = merged[merged["_element_text"]].head()

                if not recs.empty:
                    self_only_recs = list(
                        recs[
                            list(recs.columns[: self.dimension]) + ["element_text_x"]
                        ].itertuples(index=False, name=None)
                    )

                    other_only_recs = list(
                        recs[
                            list(recs.columns[: self.dimension]) + ["element_text_y"]
                        ].itertuples(index=False, name=None)
                    )

                    raise Exception(
                        "Symbol element_text does not match. First five unmatched domains: \n\n"
                        f"left_only :  {self_only_recs} \n"
                        f"right_only:  {other_only_recs} \n"
                    )


class EqualsParameterMixin(EqualsBase):
    @typing.no_type_check
    def equals(
        self,
        other: "Parameter",
        check_uels: bool = True,
        check_meta_data: bool = True,
        rtol: Optional[Union[int, float]] = None,
        atol: Optional[Union[int, float]] = None,
        verbose: bool = False,
    ) -> bool:
        """
        Used to compare the symbol to another symbol

        Parameters
        ----------
        other : Parameter
            Other Symbol to compare with
        check_uels : bool, optional
            If True, check both used and unused UELs and confirm same order, otherwise only check used UELs in data and do not check UEL order. by default True
        check_meta_data : bool, optional
            If True, check that symbol name and description are the same, otherwise skip. by default True
        rtol : int | float, optional
            relative tolerance, by default None
        atol : int | float, optional
            absolute tolerance, by default None
        verbose : bool, optional
            If True, will return an exception from the asserter describing the nature of the difference. by default False

        Returns
        -------
        bool
            True if symbols are equal, False otherwise
        """

        # check & set
        other = super().equals(other, check_uels, check_meta_data, verbose)

        # set
        columns = self._attributes

        # extension to check rtol, atol
        # ARG: rtol & atol
        if not isinstance(rtol, (type(None), int, float)):
            raise ValueError(
                "Argument 'rtol' (relative tolerance) must be "
                f"numeric (int, float) or None.  User passed: {type(rtol)}."
            )

        if not isinstance(atol, (type(None), int, float)):
            raise ValueError(
                "Argument 'atol' (relative tolerance) must be "
                f"numeric (int, float) or None.  User passed: {type(rtol)}."
            )

        # set defaults
        if rtol is None:
            rtol = 0.0

        if atol is None:
            atol = 0.0

        try:
            # check symbol attributes (not records)
            super()._assert_symbol_attributes(other, check_uels, check_meta_data)

            if self.dimension == 0:
                super()._assert_scalar_values(other, columns, rtol, atol)

            else:
                # merge records
                merged = super()._merge_records(other)

                # check domains
                super()._assert_symbol_domains(merged)

                # check values
                self._assert_symbol_values(merged, columns, rtol, atol)

            return True
        except Exception as err:
            if verbose:
                raise err
            else:
                return False

    def _assert_symbol_values(self, merged, columns, rtol, atol):
        if not merged.empty:
            for attr in columns:
                small_merged = merged[
                    list(merged.columns[: self.dimension]) + [f"{attr}_x", f"{attr}_y"]
                ].copy()

                for svlabel, SV in zip(
                    ["EPS", "NA", "UNDEF"],
                    [
                        SpecialValues.isEps,
                        SpecialValues.isNA,
                        SpecialValues.isUndef,
                    ],
                ):
                    self_idx = SV(small_merged[f"{attr}_x"])
                    other_idx = SV(small_merged[f"{attr}_y"])

                    if any(self_idx != other_idx):
                        raise Exception(
                            f"Symbol records with `{svlabel}` special values "
                            f"do not match in the `{attr}` column."
                        )

                    #
                    # drop special values if all indices match
                    small_merged.drop(index=small_merged[self_idx].index, inplace=True)

                #
                # check attr values (subject to tolerances)
                small_merged["isclose"] = np.isclose(
                    small_merged[f"{attr}_x"],
                    small_merged[f"{attr}_y"],
                    rtol=rtol,
                    atol=atol,
                )

                if any(~small_merged["isclose"]):
                    raise Exception(
                        f"Symbol records contain numeric difference in the `{attr}` attribute "
                        f"that are outside the specified tolerances (rtol={rtol}, atol={atol})"
                    )


class EqualsVariableMixin(EqualsBase):
    @typing.no_type_check
    def equals(
        self,
        other: "Variable",
        columns: str = None,
        check_uels: bool = True,
        check_meta_data: bool = True,
        rtol: Optional[Union[int, float]] = None,
        atol: Optional[Union[int, float]] = None,
        verbose: bool = False,
    ) -> bool:
        """
        Used to compare the symbol to another symbol

        Parameters
        ----------
        other : Variable
            _description_
        columns : str, optional
            allows the user to numerically compare only specified variable attributes, by default None; compare all
        check_uels : bool, optional
            If True, check both used and unused UELs and confirm same order, otherwise only check used UELs in data and do not check UEL order. by default True
        check_meta_data : bool, optional
            If True, check that symbol name and description are the same, otherwise skip. by default True
        rtol : int | float, optional
            relative tolerance, by default None
        atol : int | float, optional
            absolute tolerance, by default None
        verbose : bool, optional
            If True, will return an exception from the asserter describing the nature of the difference. by default False

        Returns
        -------
        bool
            True if symbols are equal, False otherwise
        """
        # check & set
        other = super().equals(other, check_uels, check_meta_data, verbose)

        # extension to test columns
        # ARG: columns
        if not isinstance(columns, (str, list, type(None))):
            raise TypeError(f"Argument 'columns' must be type str, list or NoneType")

        if isinstance(columns, str):
            columns = [columns]

        if columns is None:
            columns = self._attributes

        if any(i not in self._attributes for i in columns):
            raise ValueError(
                f"Argument 'columns' can only contain the following symbol attributes: {self._attributes}"
            )

        # extension to check rtol, atol
        # ARG: rtol & atol
        if not isinstance(rtol, (type(None), int, float)):
            raise ValueError(
                "Argument 'rtol' (relative tolerance) must be "
                f"numeric (int, float) or None.  User passed: {type(rtol)}."
            )

        if not isinstance(atol, (type(None), int, float)):
            raise ValueError(
                "Argument 'atol' (relative tolerance) must be "
                f"numeric (int, float) or None.  User passed: {type(rtol)}."
            )

        # set defaults
        if rtol is None:
            rtol = 0.0

        if atol is None:
            atol = 0.0

        try:
            # check symbol attributes (not records)
            super()._assert_symbol_attributes(other, check_uels, check_meta_data)

            if self.dimension == 0:
                super()._assert_scalar_values(other, columns, rtol, atol)

            else:
                # merge records
                merged = super()._merge_records(other)

                # check domains
                super()._assert_symbol_domains(merged)

                # check values
                self._assert_symbol_values(merged, columns, rtol, atol)

            return True
        except Exception as err:
            if verbose:
                raise err
            else:
                return False

    def _assert_symbol_values(self, merged, columns, rtol, atol):
        if not merged.empty:
            for attr in columns:
                small_merged = merged[
                    list(merged.columns[: self.dimension]) + [f"{attr}_x", f"{attr}_y"]
                ].copy()

                for svlabel, SV in zip(
                    ["EPS", "NA", "UNDEF"],
                    [
                        SpecialValues.isEps,
                        SpecialValues.isNA,
                        SpecialValues.isUndef,
                    ],
                ):
                    self_idx = SV(small_merged[f"{attr}_x"])
                    other_idx = SV(small_merged[f"{attr}_y"])

                    if any(self_idx != other_idx):
                        raise Exception(
                            f"Symbol records with `{svlabel}` special values "
                            f"do not match in the `{attr}` column."
                        )

                    #
                    # drop special values if all indices match
                    small_merged.drop(index=small_merged[self_idx].index, inplace=True)

                #
                # check attr values (subject to tolerances)
                small_merged["isclose"] = np.isclose(
                    small_merged[f"{attr}_x"],
                    small_merged[f"{attr}_y"],
                    rtol=rtol,
                    atol=atol,
                )

                if any(~small_merged["isclose"]):
                    raise Exception(
                        f"Symbol records contain numeric difference in the `{attr}` attribute "
                        f"that are outside the specified tolerances (rtol={rtol}, atol={atol})"
                    )


class EqualsEquationMixin(EqualsVariableMixin): ...
