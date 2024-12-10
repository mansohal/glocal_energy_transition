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

from gams.core.gmd import *
import sys
import traceback
from gams import *
from gams.control.database import _GamsSymbol


def _intValueAndFree(intP):
    intp_val = intp_value(intP)
    delete_intp(intP)
    return intp_val


class KeyFormat(object):
    TUPLE = "tuple"
    FLAT = "flat"
    SKIP = "skip"
    AUTO = "auto"


class ValueFormat(object):
    TUPLE = "tuple"
    FLAT = "flat"
    SKIP = "skip"
    AUTO = "auto"


class RecordFormat(object):
    TUPLE = "tuple"
    FLAT = "flat"
    AUTO = "auto"


class KeyType(object):
    STRING = "string"
    INT = "int"


class MergeType(object):
    REPLACE = "replace"
    MERGE = "merge"
    DEFAULT = "default"


class DomainCheckType(object):
    FILTERED = "filtered"
    CHECKED = "checked"
    DEFAULT = "default"


def merge_type_to_int(mergeType):
    if mergeType == MergeType.REPLACE:
        return 0
    if mergeType == MergeType.MERGE:
        return 1
    if mergeType == MergeType.DEFAULT:
        return 2
    raise Exception("Unexpected argument " + mergeType + " to merge_type_to_int")


def domcheck_type_to_int(domCheck):
    if domCheck == DomainCheckType.FILTERED:
        return 0
    if domCheck == DomainCheckType.CHECKED:
        return 1
    if domCheck == DomainCheckType.DEFAULT:
        return 2
    raise Exception("Unexpected argument " + domCheck + " to domcheck_type_to_int")


class ECSymbol(object):

    def __init__(
        self,
        ecDB,
        symPtr,
        keyType,
        keyFormat,
        valueFormat,
        recordFormat,
        mergeType=MergeType.DEFAULT,
        domCheck=DomainCheckType.DEFAULT,
    ):
        self._ecDB = ecDB
        self._symPtr = symPtr
        self._keyType = keyType.lower()
        self._keyFormat = keyFormat.lower()
        self._valueFormat = valueFormat.lower()
        self._recordFormat = recordFormat.lower()
        self._mergeType = mergeType.lower()
        self._domCheck = domCheck

        self._symIterPtr = None

        ret = gmdSymbolInfo(self._ecDB._gmd, self._symPtr, GMD_DIM)
        self._ecDB._check_for_gmd_error(ret[0])
        self._dim = ret[1]

        rc, type = gmdSymbolType(self._ecDB._gmd, self._symPtr)
        self._ecDB._check_for_gmd_error(rc)
        self._type = type

        if self._type == dt_par:
            self._values = self._valPar
        elif self._type in [dt_set, dt_alias]:
            self._values = self._valSet
        elif self._type in [dt_var, dt_equ]:
            self._values = self._valVarEqu

        self._setDefaultFormat()

    def __len__(self):
        ret = gmdSymbolInfo(self._ecDB._gmd, self._symPtr, GMD_NRRECORDS)
        self._ecDB._check_for_gmd_error(ret[0])
        return ret[1]

    def getSymbolNumber(self):
        ret = gmdSymbolInfo(self._ecDB._gmd, self._symPtr, GMD_NUMBER)
        self._ecDB._check_for_gmd_error(ret[0])
        return ret[1]

    def _clear(self):
        gmdClearSymbol(self._ecDB._gmd, self._symPtr)

    def _writeSet(self, parseKeys, parseValues, data, keyType):
        self._clear()
        if keyType == KeyType.STRING:
            for rec in data:
                rc = new_intp()
                symIterPtr = gmdAddRecordPy(
                    self._ecDB._gmd, self._symPtr, parseKeys(rec), rc
                )
                self._ecDB._check_for_gmd_error(_intValueAndFree(rc))
                rc = gmdSetElemText(self._ecDB._gmd, symIterPtr, parseValues(rec))
                self._ecDB._check_for_gmd_error(rc)
        elif keyType == KeyType.INT:
            keyArray = intArray(
                self._dim
            )  # TODO: move key generation into lambda function
            valueArray = doubleArray(1)
            if parseValues(next(iter(data))) != "":
                valueArray[0] = 1
            else:
                valueArray[0] = 0
            for rec in data:
                keyList = parseKeys(rec)
                for idx in range(self._dim):
                    keyArray[idx] = keyList[idx]
                rc = gmdAddRecordRaw(
                    self._ecDB._gmd,
                    self._symPtr,
                    keyArray,
                    valueArray,
                    parseValues(rec),
                )
                self._ecDB._check_for_gmd_error(rc)

    def _writeParameter(self, parseKeys, parseValues, data, keyType):
        self._clear()
        if keyType == KeyType.STRING:
            for rec in data:
                rc = new_intp()
                symIterPtr = gmdAddRecordPy(
                    self._ecDB._gmd, self._symPtr, parseKeys(rec), rc
                )
                self._ecDB._check_for_gmd_error(_intValueAndFree(rc))
                rc = gmdSetLevel(self._ecDB._gmd, symIterPtr, parseValues(rec))
                self._ecDB._check_for_gmd_error(rc)
        elif keyType == KeyType.INT:
            keyArray = intArray(
                self._dim
            )  # TODO: move key generation into lambda function
            valueArray = doubleArray(1)
            for rec in data:
                rc = new_intp()
                keyList = parseKeys(rec)
                for idx in range(self._dim):
                    keyArray[idx] = keyList[idx]
                valueArray[0] = parseValues(rec)
                rc = gmdAddRecordRaw(
                    self._ecDB._gmd, self._symPtr, keyArray, valueArray, ""
                )
                self._ecDB._check_for_gmd_error(rc)

    # TODO: combine with _writePar for reduced redundancy
    def _writeVarEqu(self, parseKeys, parseValues, data, keyType):
        self._clear()
        if keyType == KeyType.STRING:
            for rec in data:
                rc = new_intp()
                symIterPtr = gmdAddRecordPy(
                    self._ecDB._gmd, self._symPtr, parseKeys(rec), rc
                )
                self._ecDB._check_for_gmd_error(_intValueAndFree(rc))
                values = parseValues(rec)
                values = list(map(lambda x: x, values))
                rc = gmdSetLevel(self._ecDB._gmd, symIterPtr, values[0])
                self._ecDB._check_for_gmd_error(rc)
                rc = gmdSetMarginal(self._ecDB._gmd, symIterPtr, values[1])
                self._ecDB._check_for_gmd_error(rc)
                rc = gmdSetLower(self._ecDB._gmd, symIterPtr, values[2])
                self._ecDB._check_for_gmd_error(rc)
                rc = gmdSetUpper(self._ecDB._gmd, symIterPtr, values[3])
                self._ecDB._check_for_gmd_error(rc)
                rc = gmdSetScale(self._ecDB._gmd, symIterPtr, values[4])
                self._ecDB._check_for_gmd_error(rc)
        elif keyType == KeyType.INT:
            keyArray = intArray(
                self._dim
            )  # TODO: move key generation into lambda function
            valueArray = doubleArray(5)
            for rec in data:
                keyList = parseKeys(rec)
                valueList = parseValues(rec)
                for idx in range(self._dim):
                    keyArray[idx] = keyList[idx]
                for idx in range(5):
                    valueArray[idx] = valueList[idx]
                rc = gmdAddRecordRaw(
                    self._ecDB._gmd, self._symPtr, keyArray, valueArray, ""
                )
                self._ecDB._check_for_gmd_error(rc)

    def _name(self):
        ret = gmdSymbolInfo(self._ecDB._gmd, self._symPtr, GMD_NAME)
        self._ecDB._check_for_gmd_error(ret[0])
        return ret[3]

    def _setDefaultFormat(self):
        # set defaults if AUTO is specified
        if self._keyFormat == KeyFormat.AUTO:
            if self._dim == 0:
                self._keyFormat = KeyFormat.SKIP
            elif self._dim == 1:
                self._keyFormat = KeyFormat.FLAT
            else:
                self._keyFormat = KeyFormat.TUPLE
        # set defaults if AUTO is specified
        if self._valueFormat == ValueFormat.AUTO:
            if self._type in [dt_set, dt_alias]:
                self._valueFormat = ValueFormat.SKIP
            elif self._type == dt_par:
                self._valueFormat = ValueFormat.FLAT
            else:
                self._valueFormat = ValueFormat.TUPLE

        # determine possible record format
        rc = new_intp()
        self._symIterPtr = gmdFindFirstRecordPy(self._ecDB._gmd, self._symPtr, rc)
        delete_intp(rc)
        if self._symIterPtr:
            rec = self._getCurrentRecord()
            if len(rec) == 1:
                tmpRecordFormat = RecordFormat.FLAT
            else:
                tmpRecordFormat = RecordFormat.TUPLE
        else:
            tmpRecordFormat = RecordFormat.FLAT
        self._symIterPtr = None

        if self._recordFormat == RecordFormat.AUTO:
            self._recordFormat = tmpRecordFormat
        # throw exception if user wants recordFormat.FLAT but we did apply recordFormat.TUPLE. This is the only invalid setting since TUPLE can not be changed to FLAT
        elif (
            self._recordFormat == RecordFormat.FLAT
            and tmpRecordFormat == RecordFormat.TUPLE
        ):
            raise Exception("Can not apply RecordFormat.FLAT")

    def __getitem__(self, item):
        rc = new_intp()
        if type(item) is str:
            symIterPtr = gmdFindRecordPy(self._ecDB._gmd, self._symPtr, [item], rc)
        elif type(item) is int:
            pass
            # TODO: implement
        elif isinstance(item, tuple):
            symIterPtr = gmdFindRecordPy(self._ecDB._gmd, self._symPtr, list(item), rc)
        self._ecDB._check_for_gmd_error(_intValueAndFree(rc))
        val = self._values(symIterPtr)
        if len(val) == 1:
            return val[0]

    def __iter__(self):
        self._symIterPtr = None
        return self

    def __next__(self):
        return self.next()

    def next(self):
        if self._symIterPtr == None:
            rc = new_intp()
            self._symIterPtr = gmdFindFirstRecordPy(self._ecDB._gmd, self._symPtr, rc)
            delete_intp(rc)
            if self._symIterPtr == None:
                raise StopIteration
        else:
            if not gmdRecordMoveNext(self._ecDB._gmd, self._symIterPtr):
                raise StopIteration

        rec = self._getCurrentRecord()
        if self._recordFormat == RecordFormat.FLAT:
            return rec[0]
        else:
            return tuple(rec)

    def _keys(self, symIterPtr):
        if self._keyType == KeyType.STRING:
            rc, keys = gmdGetKeys(self._ecDB._gmd, symIterPtr, self._dim)
        elif self._keyType == KeyType.INT:
            rc, keys, values = gmdGetRecordRaw(self._ecDB._gmd, symIterPtr, self._dim)
        self._ecDB._check_for_gmd_error(rc)
        return tuple(keys)

    def _values(self, symIterPtr):
        raise Exception(
            "Don't call this method directly, but the implementations for the specific symbol type"
        )

    def _valSet(self, symIterPtr):
        rc, text = gmdGetElemText(self._ecDB._gmd, symIterPtr)
        self._ecDB._check_for_gmd_error(rc)
        return (text,)

    def _valPar(self, symIterPtr):
        rc, value = gmdGetLevel(self._ecDB._gmd, symIterPtr)
        if not rc:
            value = float("nan")
        if self._ecDB.epsAsZero:
            value = self._ecDB._mapEPS(value)
        return (value,)

    def _valVarEqu(self, symIterPtr):
        rc, level = gmdGetLevel(self._ecDB._gmd, symIterPtr)
        if not rc:
            level = float("nan")
        rc, marginal = gmdGetMarginal(self._ecDB._gmd, symIterPtr)
        if not rc:
            marginal = float("nan")
        rc, lower = gmdGetLower(self._ecDB._gmd, symIterPtr)
        if not rc:
            lower = float("nan")
        rc, upper = gmdGetUpper(self._ecDB._gmd, symIterPtr)
        if not rc:
            upper = float("nan")
        rc, scale = gmdGetScale(self._ecDB._gmd, symIterPtr)
        if not rc:
            scale = float("nan")
        if self._ecDB.epsAsZero:
            return tuple(
                map(
                    lambda x: self._ecDB._mapEPS(x),
                    [level, marginal, lower, upper, scale],
                )
            )
        else:
            return tuple(map(lambda x: x, [level, marginal, lower, upper, scale]))

    def _getCurrentRecord(self):
        rec = []

        if self._keyFormat == KeyFormat.TUPLE:
            rec.append(self._keys(self._symIterPtr))
        elif self._keyFormat == KeyFormat.FLAT:
            rec.extend(list(self._keys(self._symIterPtr)))
        elif self._keyFormat == KeyFormat.SKIP:
            pass

        if self._valueFormat == ValueFormat.TUPLE:
            rec.append(self._values(self._symIterPtr))
        elif self._valueFormat == ValueFormat.FLAT:
            rec.extend(list(self._values(self._symIterPtr)))
        elif self._valueFormat == ValueFormat.SKIP:
            pass

        return rec


class ECGAMSDatabase(object):

    def __init__(self, system_directory, gdx_file_name=None):
        gmdGetReady(GMS_SSSIZE)
        self._system_directory = system_directory
        self._gmd = new_gmdHandle_tp()
        self._modSymList = {}
        self._rc = 0
        self._eMsg = ""
        self.arguments = ""
        self._debug = DebugLevel.Off
        self._eps = 4.94066e-324  # copied from value in C#
        self.epsAsZero = True
        self._wsWorkingDir = None
        self._printLog = None
        self._capsule_EMBCODE_DATA = None
        self._shellcode = 0  # error code

        self._ws = None
        self._db = None
        self._cdb = None

        # create a dummy GamsWorkspace to check if system_directory is valid
        GamsWorkspace(system_directory=system_directory, debug=self._debug)

        if gdx_file_name:
            ret = gmdCreate(self._gmd, GMS_SSSIZE)
            if not ret[0]:
                raise Exception(ret[1])
            rc = gmdInitFromGDX(self._gmd, gdx_file_name)
            self._check_for_gmd_error(rc)

    def _setSpecialValue(self):
        tmp_spec_values = doubleArray(5)
        tmp_spec_values[0] = GMS_SV_UNDEF
        tmp_spec_values[1] = float("nan")
        tmp_spec_values[2] = float("inf")
        tmp_spec_values[3] = float("-inf")
        tmp_spec_values[4] = self._eps
        rc = gmdSetSpecialValues(self._gmd, tmp_spec_values)
        self._check_for_gmd_error(rc)

    def _setWsWorkingDir(self, val):
        if self._ws:
            self.printLog(
                "Warning: GamsWorkspace was already created. Setting wsWorkingDir has no effect."
            )
        else:
            self._wsWorkingDir = val

    def _getWsWorkingDir(self):
        if self._ws:
            return self._ws.working_directory
        else:
            return self._wsWorkingDir

    wsWorkingDir = property(_getWsWorkingDir, _setWsWorkingDir)

    def _setDebug(self, val):
        if self._ws:
            self.printLog(
                "Warning: GamsWorkspace was already created. Setting debug has no effect."
            )
        else:
            self._debug = val

    debug = property(None, _setDebug)

    def _getWS(self):
        if not self._ws:
            self._ws = GamsWorkspace(
                self._wsWorkingDir, self._system_directory, debug=self._debug
            )
        return self._ws

    ws = property(_getWS)

    def _getDB(self):
        if not self._db:
            self._db = self._getWS()._add_database_from_gmd(self._gmd)
            if self._getWS().my_eps != None:
                tmp_spec_values = doubleArray(GMS_SVIDX_MAX)
                rc = gmdGetUserSpecialValues(self._gmd, tmp_spec_values)
                self._check_for_gmd_error(rc)
                tmp_spec_values[GMS_SVIDX_EPS] = self._getWS().my_eps
                rc = gmdSetSpecialValues(self._gmd, tmp_spec_values)
                self._check_for_gmd_error(rc)
        return self._db

    db = property(_getDB)

    def _mapEPS(self, val):
        if val == self._eps:
            return 0
        return val

    def _printStdOut(self, msg):
        print(msg)

    def printLog(self, msg, end="\n"):
        if self._printLog and self._capsule_EMBCODE_DATA != None:
            rc = self._printLog(self._capsule_EMBCODE_DATA, msg, end)
            if not rc:
                raise Exception()
        else:
            print("*** " + msg, end=end)
            sys.stdout.flush()

    def _print_traceback_to_log(self, exception, line_offset=0):
        for frame in traceback.extract_tb(exception.__traceback__):
            self.printLog(
                f'  File "{frame.filename}", line {frame.lineno - line_offset}, in {frame.name}'
            )
            if frame.line:
                self.printLog(f"    {frame.line}")

    def print_exception_to_log(self, exception, msg, traceback=True, line_offset=0):
        if traceback:
            self._print_traceback_to_log(exception, line_offset)
        self.printLog(msg)
        sys.stdout.flush()
        sys.stderr.flush()

    def get_env(self, name):
        import os

        if os.name == "posix":
            from ctypes import CDLL, c_char_p

            getenv = CDLL(None).getenv
            getenv.restype = c_char_p
            r = getenv(name.encode())
            try:
                return r.decode()
            except:
                return None
        elif os.name == "nt":
            from ctypes import windll, create_unicode_buffer

            n = windll.kernel32.GetEnvironmentVariableW(name, None, 0)
            if n == 0:
                return None
            buf = create_unicode_buffer("\0" * n)
            windll.kernel32.GetEnvironmentVariableW(name, buf, n)
            return buf.value
        else:
            raise Exception(f"Unhandled case for os.name={os.name}")

    def _check_for_gmd_error(self, rc):
        if not rc:
            msg = gmdGetLastError(self._gmd)[1]
            raise Exception(msg)

    def getUel(self, idx):
        rc, label = gmdGetUelByIndex(self._gmd, idx)
        self._check_for_gmd_error(rc)
        return label

    def mergeUel(self, label):
        rc, idx = gmdMergeUel(self._gmd, label)
        self._check_for_gmd_error(rc)
        return idx

    def getUelCount(self):
        ret = gmdInfo(self._gmd, GMD_NRUELS)
        self._check_for_gmd_error(ret[0])
        return ret[1]

    def get(
        self,
        symbolName,
        keyType=KeyType.STRING,
        keyFormat=KeyFormat.AUTO,
        valueFormat=ValueFormat.AUTO,
        recordFormat=RecordFormat.AUTO,
    ):
        rc = new_intp()
        symPtr = gmdFindSymbolPy(self._gmd, symbolName, rc)
        self._check_for_gmd_error(_intValueAndFree(rc))
        return ECSymbol(self, symPtr, keyType, keyFormat, valueFormat, recordFormat)

    def _setSet(self, ecSymbol, data):
        firstRec = next(iter(data))
        keyType = KeyType.STRING
        parseValues = lambda rec: ""

        if not isinstance(firstRec, tuple):
            if ecSymbol._dim != 1:
                raise Exception(
                    "Error writing set '"
                    + ecSymbol._name()
                    + "': Each record needs to be represented as a tuple"
                )
            parseKeys = lambda rec: [rec]
            parseValues = lambda rec: ""
        elif isinstance(firstRec, tuple):
            if isinstance(firstRec[0], tuple):
                parseKeysX = lambda rec: list(rec[0])
                valueIdx = 1
            else:
                parseKeysX = lambda rec: list(rec[0 : ecSymbol._dim])
                valueIdx = ecSymbol._dim
            parseKeys = lambda rec: [ecSymbol._mapKeys(r) for r in parseKeysX(rec)]

            if len(firstRec) > valueIdx:
                if isinstance(firstRec[valueIdx], tuple):
                    if len(firstRec[valueIdx]) != 1:
                        raise Exception(
                            "Error writing set '"
                            + ecSymbol._name()
                            + "': Tuple representing the value needs to contain exactly one element but contains "
                            + str(len(firstRec[valueIdx]))
                            + " elements"
                        )
                    parseValues = lambda rec: rec[valueIdx][0]
                else:
                    if len(firstRec) > valueIdx + 1:
                        raise Exception(
                            "Error writing set '"
                            + ecSymbol._name()
                            + "': Exactly one value is expected for parameter value"
                        )
                    parseValues = lambda rec: rec[valueIdx]

            if len(parseKeys(firstRec)) != ecSymbol._dim:
                raise Exception(
                    "Error writing set '"
                    + ecSymbol._name()
                    + "': Number of keys ("
                    + str(len(parseKeys(firstRec)))
                    + ") doesn't match the symbol dimension ("
                    + str(ecSymbol._dim)
                )

        sawInt = False
        sawString = False
        for k in parseKeys(firstRec):
            if isinstance(k, int):
                sawInt = True
                keyType = KeyType.INT
            elif type(k) is str:
                sawString = True
                keyType = KeyType.STRING
            else:
                raise Exception(
                    "Error writing set '"
                    + ecSymbol._name()
                    + "': Expecting keys to be of type str or int"
                )
            if sawInt and sawString:
                raise Exception(
                    "Error writing set '"
                    + ecSymbol._name()
                    + "': Mixed key types (int and str) are not allowed"
                )
        if not type(parseValues(firstRec)) is str:
            raise Exception(
                "Error writing set '" + ecSymbol._name() + "': Value needs to be str"
            )

        ecSymbol._writeSet(parseKeys, parseValues, data, keyType)

    def _setPar(self, ecSymbol, data):
        firstRec = next(iter(data))
        keyType = KeyType.STRING

        # handle scalars
        if ecSymbol._dim == 0:
            if len(data) != 1:
                raise Exception(
                    "Error writing scalar '"
                    + ecSymbol._name()
                    + "': Length of data needs to be 1 but is "
                    + str(len(data))
                )
            if self._isNumeric(firstRec):
                parseKeys = lambda rec: []
                parseValues = lambda rec: rec
            elif isinstance(firstRec, tuple):
                if len(firstRec) != 1:
                    raise Exception(
                        "Error writing scalar '"
                        + ecSymbol._name()
                        + "': Length of tuple containing the scalar value needs to be 1 but is"
                        + str(len(firstRec))
                    )
                if not self._isNumeric(firstRec[0]):
                    raise Exception(
                        "Error writing scalar '"
                        + ecSymbol._name()
                        + "': Element in tuple needs to be numeric"
                    )
                parseKeys = lambda rec: []
                parseValues = lambda rec: rec[0]

            else:
                raise Exception(
                    "Error writing scalar '"
                    + ecSymbol._name()
                    + "': Data format not accepted"
                )

        # handle parameters with dim>=1
        if ecSymbol._dim > 0:
            if not isinstance(firstRec, tuple):
                raise Exception(
                    "Error writing parameter '"
                    + ecSymbol._name()
                    + "': Each record needs to be represented as a tuple"
                )
            if isinstance(firstRec[0], tuple):
                parseKeysX = lambda rec: list(rec[0])
                valueIdx = 1
            else:
                parseKeysX = lambda rec: list(rec[0 : ecSymbol._dim])
                valueIdx = ecSymbol._dim
            parseKeys = lambda rec: [ecSymbol._mapKeys(r) for r in parseKeysX(rec)]

            if len(parseKeys(firstRec)) != ecSymbol._dim:
                raise Exception(
                    "Error writing parameter '"
                    + ecSymbol._name()
                    + "': Number of keys ("
                    + str(len(parseKeys(firstRec)))
                    + ") doesn't match the symbol dimension ("
                    + str(ecSymbol._dim)
                )

            if isinstance(firstRec[valueIdx], tuple):
                if len(firstRec[valueIdx]) != 1:
                    raise Exception(
                        "Error writing parameter '"
                        + ecSymbol._name()
                        + "': Tuple representing the value needs to contain exactly one element but contains "
                        + str(len(firstRec[valueIdx]))
                        + " elements"
                    )
                parseValues = lambda rec: rec[valueIdx][0]
            else:
                parseValues = lambda rec: rec[valueIdx]
                if len(firstRec) > valueIdx + 1:
                    raise Exception(
                        "Error writing parameter '"
                        + ecSymbol._name()
                        + "': Exactly one value is expected for parameter value"
                    )

        sawInt = False
        sawString = False
        for k in parseKeys(firstRec):
            if isinstance(k, int):
                sawInt = True
                keyType = KeyType.INT
            elif type(k) is str:
                sawString = True
                keyType = KeyType.STRING
            else:
                raise Exception(
                    "Error writing parameter '"
                    + ecSymbol._name()
                    + "': Expecting keys to be of type str or int"
                )
            if sawInt and sawString:
                raise Exception(
                    "Error writing parameter '"
                    + ecSymbol._name()
                    + "': Mixed key types (int and str) are not allowed"
                )
        if not self._isNumeric(parseValues(firstRec)):
            raise Exception(
                "Error writing parameter '"
                + ecSymbol._name()
                + "': Value needs to be numeric"
            )

        ecSymbol._writeParameter(parseKeys, parseValues, data, keyType)

    # TODO: combine with _setPar in order to avoid redundant code
    def _setVarEqu(self, ecSymbol, data):
        firstRec = next(iter(data))
        keyType = KeyType.STRING

        # handle scalar variables
        if ecSymbol._dim == 0:
            if len(data) != 1:
                raise Exception(
                    "Error writing scalar variable/equation '"
                    + ecSymbol._name()
                    + "': Length of data needs to be 1 but is "
                    + str(len(data))
                )
            if not isinstance(firstRec, tuple):
                raise Exception(
                    "Error writing scalar variable/equation '"
                    + ecSymbol._name()
                    + "': Record needs to be represented as tuple"
                )
            if not len(firstRec) == 5:
                raise Exception(
                    "Error writing scalar variable/equation '"
                    + ecSymbol._name()
                    + "': Record needs to consist of 5 values, but found "
                    + str(len(firstRecord))
                )
            for v in firstRec:
                if not self._isNumeric(v):
                    raise Exception(
                        "Error writing scalar variable/equation '"
                        + ecSymbol._name()
                        + "': Values need to be numeric"
                    )
            parseKeys = lambda rec: []
            parseValues = lambda rec: list(rec)

        # handle variables with dim>=1
        if ecSymbol._dim > 0:
            if not isinstance(firstRec, tuple):
                raise Exception(
                    "Error writing variable/equation '"
                    + ecSymbol._name()
                    + "': Each record needs to be represented as a tuple"
                )
            if isinstance(firstRec[0], tuple):
                parseKeysX = lambda rec: list(rec[0])
                valueIdx = 1
            else:
                parseKeysX = lambda rec: list(rec[0 : ecSymbol._dim])
                valueIdx = ecSymbol._dim
            parseKeys = lambda rec: [ecSymbol._mapKeys(r) for r in parseKeysX(rec)]

            if len(parseKeys(firstRec)) != ecSymbol._dim:
                raise Exception(
                    "Error writing variable/equation '"
                    + ecSymbol._name()
                    + "': Number of keys ("
                    + str(len(parseKeys(firstRec)))
                    + ") doesn't match the symbol dimension ("
                    + str(ecSymbol._dim)
                )

            if isinstance(firstRec[valueIdx], tuple):
                if len(firstRec[valueIdx]) != 5:
                    raise Exception(
                        "Error writing variable/equation '"
                        + ecSymbol._name()
                        + "': Tuple representing the value needs to contain exactly five element but contains "
                        + str(len(firstRec[valueIdx]))
                        + " elements"
                    )
                parseValues = lambda rec: rec[valueIdx]
            else:
                parseValues = lambda rec: rec[valueIdx : valueIdx + 5]
                if len(firstRec) > valueIdx + 5:
                    raise Exception(
                        "Error writing variable/equation '"
                        + ecSymbol._name()
                        + "': Exactly 5 values are expected for parameter value"
                    )

        sawInt = False
        sawString = False
        for k in parseKeys(firstRec):
            if isinstance(k, int):
                sawInt = True
                keyType = KeyType.INT
            elif type(k) is str:
                sawString = True
                keyType = KeyType.STRING
            else:
                raise Exception(
                    "Error writing variable/equation '"
                    + ecSymbol._name()
                    + "': Expecting keys to be of type str or int"
                )
            if sawInt and sawString:
                raise Exception(
                    "Error writing variable/equation '"
                    + ecSymbol._name()
                    + "': Mixed key types (int and str) are not allowed"
                )

        for v in parseValues(firstRec):
            if not self._isNumeric(v):
                raise Exception(
                    "Error writing variable/equation '"
                    + ecSymbol._name()
                    + "': Value needs to be numeric"
                )

        ecSymbol._writeVarEqu(parseKeys, parseValues, data, keyType)

    def set(
        self,
        symbolName,
        data,
        mergeType=MergeType.DEFAULT,
        domCheck=DomainCheckType.DEFAULT,
        mapKeys=lambda x: x,
    ):
        if (
            not isinstance(data, list)
            and not isinstance(data, set)
            and not isinstance(data, _GamsSymbol)
        ):
            raise Exception("Data needs to be a list or a set")

        ecSymbol = self.get(symbolName)
        ecSymbol._mergeType = mergeType
        ecSymbol._domCheck = domCheck
        ecSymbol._mapKeys = mapKeys
        if isinstance(data, _GamsSymbol):
            if (
                data._sym_ptr == ecSymbol._symPtr
            ):  # same symbol, no copy of data required
                pass
            else:
                gmdCopySymbol(data._database._gmd, ecSymbol._symPtr, data._sym_ptr)

        elif len(data) == 0:
            ecSymbol._clear()
        elif ecSymbol._type == dt_par:
            self._setPar(ecSymbol, data)
        elif ecSymbol._type in [dt_var, dt_equ]:
            self._setVarEqu(ecSymbol, data)
        elif ecSymbol._type == dt_set:
            self._setSet(ecSymbol, data)

        self._modSymList[ecSymbol.getSymbolNumber()] = (
            merge_type_to_int(ecSymbol._mergeType),
            domcheck_type_to_int(ecSymbol._domCheck),
        )

    def _isNumeric(self, element):
        return isinstance(element, float) or isinstance(element, int)
