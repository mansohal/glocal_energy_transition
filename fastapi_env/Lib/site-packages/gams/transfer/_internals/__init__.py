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

from gams.transfer._internals.casepreservingdict import CasePreservingDict

from gams.transfer._internals.specialvalues import SpecialValues

from gams.transfer._internals.constants import (
    GAMS_SYMBOL_MAX_LENGTH,
    GAMS_UEL_MAX_LENGTH,
    GAMS_DESCRIPTION_MAX_LENGTH,
    GAMS_MAX_INDEX_DIM,
    SourceType,
    DestinationType,
    DomainStatus,
    DictFormat,
    EPS,
    UNDEF,
    NA,
    VAR_DEFAULT_VALUES,
    EQU_TYPE,
    EQU_DEFAULT_VALUES,
    DICT_FORMAT,
    GAMS_VARIABLE_SUBTYPES,
    GAMS_EQUATION_SUBTYPES,
    TRANSFER_TO_GAMS_VARIABLE_SUBTYPES,
    TRANSFER_TO_GAMS_EQUATION_SUBTYPES,
    GAMS_DOMAIN_STATUS,
)

from gams.transfer._internals.domainviolation import DomainViolation

from gams.transfer._internals.algorithms import (
    cartesian_product,
    choice_no_replace,
    generate_unique_labels,
    convert_to_categoricals_cat,
    convert_to_categoricals_str,
    get_keys_and_values,
    check_all_same,
)
