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
from enum import Enum
from gams.core.gdx import GMS_UEL_IDENT_SIZE, GMS_SSSIZE, GMS_MAX_INDEX_DIM
from gams.core.gdx import GMS_DT_SET, GMS_DT_ALIAS, GMS_DT_PAR, GMS_DT_VAR, GMS_DT_EQU
from gams.core.gdx import (
    GMS_VARTYPE_FREE,
    GMS_VARTYPE_BINARY,
    GMS_VARTYPE_INTEGER,
    GMS_VARTYPE_NEGATIVE,
    GMS_VARTYPE_POSITIVE,
    GMS_VARTYPE_SEMICONT,
    GMS_VARTYPE_SEMIINT,
    GMS_VARTYPE_SOS1,
    GMS_VARTYPE_SOS2,
)
from gams.core.gdx import (
    GMS_EQUTYPE_B,
    GMS_EQUTYPE_C,
    GMS_EQUTYPE_E,
    GMS_EQUTYPE_G,
    GMS_EQUTYPE_L,
    GMS_EQUTYPE_N,
    GMS_EQUTYPE_X,
)
from gams.transfer._internals import SpecialValues

GAMS_SYMBOL_MAX_LENGTH = GMS_UEL_IDENT_SIZE - 1
GAMS_UEL_MAX_LENGTH = GMS_UEL_IDENT_SIZE - 1
GAMS_DESCRIPTION_MAX_LENGTH = GMS_SSSIZE - 1
GAMS_MAX_INDEX_DIM = GMS_MAX_INDEX_DIM


class DictFormat(Enum):
    UNKNOWN = -1
    COLUMNS = 0
    NATURAL = 1

    @classmethod
    def _missing_(cls, value):
        return DictFormat.UNKNOWN


DICT_FORMAT = {
    "natural": DictFormat.NATURAL,
    "columns": DictFormat.COLUMNS,
}


class SourceType(Enum):
    UNKNOWN = -1
    GDX = 0
    GMD = 1
    CONTAINER = 2

    @classmethod
    def _missing_(cls, value):
        return SourceType.UNKNOWN


class DestinationType(Enum):
    UNKNOWN = -1
    GDX = 0
    GMD = 1

    @classmethod
    def _missing_(cls, value):
        return DestinationType.UNKNOWN


class DomainStatus(Enum):
    UNKNOWN = 0
    none = 1
    relaxed = 2
    regular = 3

    @classmethod
    def _missing_(cls, value):
        return DomainStatus.UNKNOWN


GAMS_DOMAIN_STATUS = {1: "none", 2: "relaxed", 3: "regular"}


GAMS_VARIABLE_SUBTYPES = {
    GMS_VARTYPE_BINARY: "binary",
    GMS_VARTYPE_INTEGER: "integer",
    GMS_VARTYPE_POSITIVE: "positive",
    GMS_VARTYPE_NEGATIVE: "negative",
    GMS_VARTYPE_FREE: "free",
    GMS_VARTYPE_SOS1: "sos1",
    GMS_VARTYPE_SOS2: "sos2",
    GMS_VARTYPE_SEMICONT: "semicont",
    GMS_VARTYPE_SEMIINT: "semiint",
}

TRANSFER_TO_GAMS_VARIABLE_SUBTYPES = {v: k for k, v in GAMS_VARIABLE_SUBTYPES.items()}

GAMS_EQUATION_SUBTYPES = {
    GMS_EQUTYPE_E: "eq",
    GMS_EQUTYPE_G: "geq",
    GMS_EQUTYPE_L: "leq",
    GMS_EQUTYPE_N: "nonbinding",
    GMS_EQUTYPE_X: "external",
    GMS_EQUTYPE_C: "cone",
    GMS_EQUTYPE_B: "boolean",
}

TRANSFER_TO_GAMS_EQUATION_SUBTYPES = {v: k for k, v in GAMS_EQUATION_SUBTYPES.items()}


VAR_DEFAULT_VALUES = {
    "binary": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": 1.0,
        "scale": 1.0,
    },
    "integer": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "positive": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "negative": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": SpecialValues.NEGINF,
        "upper": 0.0,
        "scale": 1.0,
    },
    "free": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": SpecialValues.NEGINF,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "sos1": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "sos2": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "semicont": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 1.0,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "semiint": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 1.0,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
}

# equation types
EQU_TYPE = {
    "eq": "eq",
    "geq": "geq",
    "leq": "leq",
    "nonbinding": "nonbinding",
    "cone": "cone",
    "external": "external",
    "boolean": "boolean",
}

# additional user supported notation for defining equation types
EQU_TYPE.update({"=e=": "eq", "e": "eq"})
EQU_TYPE.update({"=g=": "geq", "g": "geq"})
EQU_TYPE.update({"=l=": "leq", "l": "leq"})
EQU_TYPE.update({"=n=": "nonbinding", "n": "nonbinding"})
EQU_TYPE.update({"=x=": "external", "x": "external"})
EQU_TYPE.update({"=c=": "cone", "c": "cone"})
EQU_TYPE.update({"=b=": "boolean", "b": "boolean"})

EQU_DEFAULT_VALUES = {
    "eq": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": 0.0,
        "scale": 1.0,
    },
    "geq": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "leq": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": SpecialValues.NEGINF,
        "upper": 0.0,
        "scale": 1.0,
    },
    "nonbinding": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": SpecialValues.NEGINF,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "cone": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": SpecialValues.POSINF,
        "scale": 1.0,
    },
    "external": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": 0.0,
        "scale": 1.0,
    },
    "boolean": {
        "level": 0.0,
        "marginal": 0.0,
        "lower": 0.0,
        "upper": 0.0,
        "scale": 1.0,
    },
}


# equivalents
EPS = set(list(map("".join, itertools.product(*zip("EPS", "eps")))))
UNDEF = set(
    list(map("".join, itertools.product(*zip("UNDEF", "undef"))))
    + list(map("".join, itertools.product(*zip("UNDF", "undf"))))
)
NA = set(list(map("".join, itertools.product(*zip("NA", "na")))))
