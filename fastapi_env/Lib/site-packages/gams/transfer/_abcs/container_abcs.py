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

from abc import ABC, abstractmethod


class AnyContainerSymbol: ...


class AnyContainerDomainSymbol: ...


class AnyContainerAlias: ...


class ABC_SAPVE_Container(ABC):
    @abstractmethod
    def __init__(self): ...

    @abstractmethod
    def __repr__(self): ...

    @abstractmethod
    def _assert_is_valid(self): ...

    @abstractmethod
    def countDomainViolations(self): ...

    @abstractmethod
    def countDuplicateRecords(self): ...

    @abstractmethod
    def dropDomainViolations(self): ...

    @abstractmethod
    def dropDuplicateRecords(self): ...

    @abstractmethod
    def getDomainViolations(self): ...

    @abstractmethod
    def getUELs(self): ...

    @abstractmethod
    def lowerUELs(self): ...

    @abstractmethod
    def upperUELs(self): ...

    @abstractmethod
    def lstripUELs(self): ...

    @abstractmethod
    def rstripUELs(self): ...

    @abstractmethod
    def stripUELs(self): ...

    @abstractmethod
    def capitalizeUELs(self): ...

    @abstractmethod
    def casefoldUELs(self): ...

    @abstractmethod
    def titleUELs(self): ...

    @abstractmethod
    def ljustUELs(self): ...

    @abstractmethod
    def rjustUELs(self): ...

    @abstractmethod
    def hasDomainViolations(self): ...

    @abstractmethod
    def hasDuplicateRecords(self): ...

    @abstractmethod
    def isValid(self): ...

    @abstractmethod
    def modified(self): ...

    @abstractmethod
    def removeUELs(self): ...

    @abstractmethod
    def renameUELs(self): ...


class ABC_SAPVE_UA(ABC):
    @abstractmethod
    def __init__(self): ...

    @abstractmethod
    def __repr__(self): ...

    @abstractmethod
    def _assert_is_valid(self): ...

    @abstractmethod
    def description(self): ...

    @abstractmethod
    def dimension(self): ...

    @abstractmethod
    def domain(self): ...

    @abstractmethod
    def domain_labels(self): ...

    @abstractmethod
    def domain_names(self): ...

    @abstractmethod
    def domain_type(self): ...

    @abstractmethod
    def equals(self): ...

    @abstractmethod
    def getSparsity(self): ...

    @abstractmethod
    def getUELs(self): ...

    @abstractmethod
    def isValid(self): ...

    @abstractmethod
    def modified(self): ...

    @abstractmethod
    def name(self): ...

    @abstractmethod
    def number_records(self): ...

    @abstractmethod
    def pivot(self): ...

    @abstractmethod
    def records(self): ...

    @abstractmethod
    def container(self): ...

    @abstractmethod
    def summary(self): ...

    @abstractmethod
    def toList(self): ...


class ABC_SAPVE(ABC):
    @abstractmethod
    def _getUELCodes(self): ...

    @abstractmethod
    def addUELs(self): ...

    @abstractmethod
    def countDomainViolations(self): ...

    @abstractmethod
    def countDuplicateRecords(self): ...

    @abstractmethod
    def dropDomainViolations(self): ...

    @abstractmethod
    def dropDuplicateRecords(self): ...

    @abstractmethod
    def findDomainViolations(self): ...

    @abstractmethod
    def findDuplicateRecords(self): ...

    @abstractmethod
    def getDomainViolations(self): ...

    @abstractmethod
    def hasDomainViolations(self): ...

    @abstractmethod
    def hasDuplicateRecords(self): ...

    @abstractmethod
    def removeUELs(self): ...

    @abstractmethod
    def renameUELs(self): ...

    @abstractmethod
    def reorderUELs(self): ...

    @abstractmethod
    def setRecords(self): ...

    @abstractmethod
    def setUELs(self): ...


class ABC_SPVE(ABC):
    @abstractmethod
    def _assert_scalar_values(self): ...

    @abstractmethod
    def _assert_symbol_attributes(self): ...

    @abstractmethod
    def _assert_symbol_domains(self): ...

    @abstractmethod
    def _attributes(self): ...

    @abstractmethod
    def _domainForwarding(self): ...

    @abstractmethod
    def _merge_records(self): ...

    @abstractmethod
    def domain_forwarding(self): ...

    @abstractmethod
    def _domain_status(self): ...

    @abstractmethod
    def generateRecords(self): ...


class ABC_SAUA(ABC):
    @abstractmethod
    def is_singleton(self): ...


class ABC_PVE(ABC):
    @abstractmethod
    def _assert_symbol_values(self): ...

    @abstractmethod
    def _filter_zero_records(self): ...

    @abstractmethod
    def _countSpecialValues(self): ...

    @abstractmethod
    def _getMetric(self): ...

    @abstractmethod
    def _whereMetric(self): ...

    @abstractmethod
    def countEps(self): ...

    @abstractmethod
    def countNA(self): ...

    @abstractmethod
    def countNegInf(self): ...

    @abstractmethod
    def countPosInf(self): ...

    @abstractmethod
    def countUndef(self): ...

    @abstractmethod
    def findEps(self): ...

    @abstractmethod
    def findNA(self): ...

    @abstractmethod
    def findNegInf(self): ...

    @abstractmethod
    def findPosInf(self): ...

    @abstractmethod
    def findSpecialValues(self): ...

    @abstractmethod
    def findUndef(self): ...

    @abstractmethod
    def getMaxAbsValue(self): ...

    @abstractmethod
    def getMaxValue(self): ...

    @abstractmethod
    def getMeanValue(self): ...

    @abstractmethod
    def getMinValue(self): ...

    @abstractmethod
    def is_scalar(self): ...

    @abstractmethod
    def shape(self): ...

    @abstractmethod
    def toDense(self): ...

    @abstractmethod
    def toDict(self): ...

    @abstractmethod
    def toSparseCoo(self): ...

    @abstractmethod
    def toValue(self): ...

    @abstractmethod
    def whereMax(self): ...

    @abstractmethod
    def whereMaxAbs(self): ...

    @abstractmethod
    def whereMin(self): ...


class ABC_VE(ABC):
    @abstractmethod
    def type(self): ...


class ABC_AUA(ABC):
    @abstractmethod
    def alias_with(self): ...


class ABCSet(
    AnyContainerSymbol,
    AnyContainerDomainSymbol,
    ABC_SAPVE_Container,
    ABC_SAPVE_UA,
    ABC_SAPVE,
    ABC_SPVE,
    ABC_SAUA,
): ...


class ABCParameter(
    AnyContainerSymbol,
    ABC_SAPVE_Container,
    ABC_SAPVE_UA,
    ABC_SAPVE,
    ABC_SPVE,
    ABC_PVE,
): ...


class ABCVariable(
    AnyContainerSymbol,
    ABC_SAPVE_Container,
    ABC_SAPVE_UA,
    ABC_SAPVE,
    ABC_SPVE,
    ABC_PVE,
    ABC_VE,
): ...


class ABCEquation(
    AnyContainerSymbol,
    ABC_SAPVE_Container,
    ABC_SAPVE_UA,
    ABC_SAPVE,
    ABC_SPVE,
    ABC_PVE,
    ABC_VE,
): ...


class ABCAlias(
    AnyContainerSymbol,
    AnyContainerDomainSymbol,
    AnyContainerAlias,
    ABC_SAPVE_Container,
    ABC_SAPVE_UA,
    ABC_SAPVE,
    ABC_SAUA,
    ABC_AUA,
): ...


class ABCUniverseAlias(
    AnyContainerSymbol,
    AnyContainerDomainSymbol,
    AnyContainerAlias,
    ABC_SAPVE_UA,
    ABC_SAUA,
    ABC_AUA,
): ...


class ABCContainer(ABC_SAPVE_Container):
    @abstractmethod
    def summary(self): ...

    @abstractmethod
    def hasSymbols(self): ...
