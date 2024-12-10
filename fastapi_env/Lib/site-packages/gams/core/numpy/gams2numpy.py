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

from gams.core.numpy import _gams2numpy
from gams.core.gdx import *
from gams.core.gmd import *
from gams.control.database import GamsDatabase, _GamsSymbol
from gams.control.workspace import GamsWorkspace
import numpy as np
from enum import Enum


class Mode(Enum):
    RAW = 0
    STRING = 1
    MAP = 2
    CATEGORICAL = 3


class Gams2Numpy(object):
    def __init__(self, system_directory=None):
        if system_directory:
            ws = GamsWorkspace(system_directory=system_directory)
        else:
            ws = GamsWorkspace()
        self._system_directory = ws.system_directory
        _gams2numpy.getReady(self._system_directory)

    def _get_system_directory(self):
        return self._system_directory

    ## @brief GAMS system directory
    system_directory = property(_get_system_directory)

    def _convertNoneArrays(self, arrKeys, arrValues, symType, raw):
        if arrValues is None and arrKeys is None:
            raise Exception("Not both arrKeys and arrValues can be None")
        if symType in [GMS_DT_SET, GMS_DT_ALIAS] and arrValues is None:
            arrValues = np.full((arrKeys.shape[0], 1), "", dtype=object)
        if symType in [GMS_DT_PAR, GMS_DT_VAR, GMS_DT_EQU] and arrKeys is None:
            if raw:
                arrKeys = np.full((arrValues.shape[0], 0), "", dtype=int)
            else:
                arrKeys = np.full((arrValues.shape[0], 0), "", dtype=object)
        return arrKeys, arrValues

    def _validateTypes(self, arrKeys, arrValues, symType, raw):
        if raw:
            if arrKeys.dtype not in [
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
            ]:
                raise Exception(
                    f"Wrong dtype for arrKeys in 'raw/map' mode. Got type {arrKeys.dtype}, but requires np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, or np.uint32"
                )
        else:
            if arrKeys.dtype != object:
                raise Exception(
                    f"Wrong dtype for arrKeys in 'string' mode. Got type {arrKeys.dtype}, but requires object"
                )
        if symType in [GMS_DT_SET, GMS_DT_ALIAS]:
            if arrValues.dtype != object:
                raise Exception(
                    f"Wrong dtype for arrValues. Got type {arrValues.dtype}, but requires object"
                )
        else:
            if arrValues.dtype != np.float64:
                raise Exception(
                    f"Wrong dtype for arrValues. Got type {arrValues.dtype}, but requires np.float64"
                )

    def _validateKeyArray(self, arr, symDim):
        if len(arr.shape) != 2:
            raise Exception("Numpy array needs to have exactly two dimensions")

        if arr.shape[1] != symDim:
            raise Exception("Unexpected number of columns")

    def _validateValueArray(self, arr, symType):
        if len(arr.shape) != 2:
            raise Exception("Numpy array needs to have exactly two dimensions")
        expectedCols = 1
        if symType in [GMS_DT_VAR, GMS_DT_EQU]:
            expectedCols = GMS_VAL_MAX

        if arr.shape[1] != expectedCols:
            if (
                symType in [GMS_DT_SET, GMS_DT_ALIAS] and arr.shape[1] == 0
            ):  # for sets we allow to skip the explanatory text
                pass
            else:
                raise Exception("Unexpected number of columns")

    def _convertKeyTypes(self, arr, raw):
        if raw:
            arr2 = arr.astype(int)
        else:
            arr2 = arr.astype(str).astype(object)
        return arr2

    def _convertValueTypes(self, arr, symType):
        if symType in [GMS_DT_SET, GMS_DT_ALIAS]:
            arr2 = arr.astype(str).astype(object)
        else:
            arr2 = arr.astype(float)
        return arr2

    def _convertMemoryLayouts(self, arrKeys, arrValues, mode, symType):
        # handle numpy memory layout and enforce C-layout if necessary
        if (
            mode != Mode.STRING
            and not arrKeys.flags.carray
            and not arrKeys.flags.farray
        ):
            arrKeys = np.array(arrKeys, order="C", copy=True)
        if (
            symType in [GMS_DT_PAR, GMS_DT_VAR, GMS_DT_EQU]
            and not arrValues.flags.carray
            and not arrValues.flags.farray
        ):
            arrValues = np.array(arrValues, order="C", copy=True)
        return arrKeys, arrValues

    # @brief Register multiple UELs
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp'.
    # @param uels List of labels (str) to be registered as UELs.
    # @return None
    def gdxRegisterUels(self, gdx, uels):
        """
        Register multiple UELs

        Parameters
        ----------
        gdx : GDX handle
            GDX handle created with 'gdxcc.new_gdxHandle_tp'.
        uels : _type_
            List of labels (str) to be registered as UELs.
        """

        return _gams2numpy.gdxRegisterUels(gdxHandleToPtr(gdx), uels)

    # @brief Register multiple UELs
    # @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
    # @param uels List of labels (str) to be registered as UELs.
    # @return None
    def gmdRegisterUels(self, gmd, uels):
        """
        Register multiple UELs

        Parameters
        ----------
        gmd : GMD handle
            GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
        uels : List[str]
            List of labels (str) to be registered as UELs.
        """
        if isinstance(gmd, GamsDatabase):
            gmdH = gmd._gmd
        else:
            gmdH = gmd
        return _gams2numpy.gmdRegisterUels(gmdHandleToPtr(gmdH), uels)

    # @brief Retrieve the list of UELs.
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
    # @param encoding The name of the encoding, default None means utf-8.
    # @return List of UELs.
    def gdxGetUelList(self, gdx, encoding=None):
        """
        Retrieve the list of UELs.

        Parameters
        ----------
        gdx : GDX handle
            GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
        encoding : str, optional
            The name of the encoding, default None means utf-8.

        Returns
        -------
        List[str]
            List of UELs.
        """
        if isinstance(gdx, str):  # treat parameter 'gdx' as file name
            gdxHandle = new_gdxHandle_tp()
            rc, msg = gdxCreateD(gdxHandle, self._system_directory, GMS_SSSIZE)
            if not rc:
                raise Exception(msg)
            if not gdxOpenRead(gdxHandle, gdx)[0]:
                raise Exception("Error opening GDX file " + gdx)
            ret = _gams2numpy.gdxGetUelList(gdxHandleToPtr(gdxHandle), encoding)
            gdxClose(gdxHandle)
            gdxFree(gdxHandle)
            return ret
        else:  # treat parameter 'gdx' as GDX handle
            return _gams2numpy.gdxGetUelList(gdxHandleToPtr(gdx), encoding)

    def _gdxGetSymbolExplTxt(self, gdx, symNr, encoding=None):
        """
        @brief Retrieve a symbol's explanatory text, possibly decoded.
        @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
        @param symNr The symbol number of the GDX symbol to retrieve the explanatory text from.
        @param encoding The name of the encoding, default None means utf-8.
        @return PyObject str with explanatory text.
        """
        if isinstance(gdx, str):  # treat parameter 'gdx' as file name
            gdxHandle = new_gdxHandle_tp()
            rc, msg = gdxCreateD(gdxHandle, self._system_directory, GMS_SSSIZE)
            if not rc:
                raise Exception(msg)
            if not gdxOpenRead(gdxHandle, gdx)[0]:
                raise Exception("Error opening GDX file " + gdx)
            ret = _gams2numpy.gdxGetSymbolExplTxt(
                gdxHandleToPtr(gdxHandle), symNr, encoding
            )
            gdxClose(gdxHandle)
            gdxFree(gdxHandle)
            return ret
        else:  # treat parameter 'gdx' as GDX handle
            return _gams2numpy.gdxGetSymbolExplTxt(gdxHandleToPtr(gdx), symNr, encoding)

    def _gmdGetSymbolExplTxt(self, gmd, symbolPtr, encoding=None):
        """
        @brief Retrieve a symbol's explanatory text, possibly decoded.
        @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
        @param symbolPtr GMD symbol pointer or an instance of GamsParamater, GamsSet, GamsVariable or GamsEquation.
        @param encoding The name of the encoding, default None means utf-8.
        @return PyObject str with explanatory text.
        """
        if isinstance(gmd, GamsDatabase):
            gmdH = gmd._gmd
        else:
            gmdH = gmd
        if isinstance(symbolPtr, _GamsSymbol):
            symPtr = symbolPtr._sym_ptr
        else:
            symPtr = symbolPtr
        return _gams2numpy.gmdGetSymbolExplTxt(gmdHandleToPtr(gmdH), symPtr, encoding)

    # @brief Retrieve the list of UELs.
    # @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
    # @param encoding The name of the encoding, default None means utf-8.
    # @return List of UELs.
    def gmdGetUelList(self, gmd, encoding=None):
        """
        Retrieve the list of UELs.

        Parameters
        ----------
        gmd : GMD handle
            GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
        encoding : str, optional
            The name of the encoding, default None means utf-8.

        Returns
        -------
        List[str]
            List of UELs.
        """
        if isinstance(gmd, GamsDatabase):
            gmdH = gmd._gmd
        else:
            gmdH = gmd
        return _gams2numpy.gmdGetUelList(gmdHandleToPtr(gmdH), encoding)

    def _gdxReadSymbol(self, gdx, symName, mode, uelList=None, encoding=None):
        if not isinstance(mode, Mode):
            raise Exception(
                "Unknown mode. Specify either Mode.RAW, Mode.STRING, or Mode.CATEGORICAL."
            )

        if isinstance(gdx, str):  # treat parameter 'gdx' as file name
            gdxHandle = new_gdxHandle_tp()
            rc, msg = gdxCreateD(gdxHandle, self._system_directory, GMS_SSSIZE)
            if not rc:
                raise Exception(msg)
            if not gdxOpenRead(gdxHandle, gdx)[0]:
                raise Exception("Error opening GDX file " + gdx)
            ret = _gams2numpy.gdxReadSymbol(
                gdxHandleToPtr(gdxHandle), symName, mode.value, uelList, encoding
            )
            gdxClose(gdxHandle)
            gdxFree(gdxHandle)
            return ret
        else:  # treat parameter 'gdx' as GDX handle
            return _gams2numpy.gdxReadSymbol(
                gdxHandleToPtr(gdx), symName, mode.value, uelList, encoding
            )

    # @brief Reads symbol data from GDX into two numpy arrays, one for keys (object<str>) and one for values (object<str> or float).
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
    # @param symName The name of the symbol to be read.
    # @param uelList List of UELs to be used for mapping internal numbers to labels, usually retrieved by 'gdxGetUelList'. If omitted, the UEL list is generated internally from the GDX file.
    #         Supplying this parameter can increase performance when reading multiple symbols from the same GDX file since the UEL list creation has to be performed only once.
    # @param encoding The name of the encoding, default None means utf-8.
    # @return Two numpy arrays - one for the keys (object<str>) and one for the values (object<str> or float).
    def gdxReadSymbolStr(self, gdx, symName, uelList=None, encoding=None):
        """
        Reads symbol data from GDX into two numpy arrays, one for keys (object<str>) and one for values (object<str> or float).

        Parameters
        ----------
        gdx : GDX handle | str
            GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
        symName : str
            The name of the symbol to be read.
        uelList : List[str], optional
            List of UELs to be used for mapping internal numbers to labels, usually retrieved by 'gdxGetUelList'. If omitted, the UEL list is generated internally from the GDX file.
            Supplying this parameter can increase performance when reading multiple symbols from the same GDX file since the UEL list creation has to be performed only once.
        encoding : str, optional
            The name of the encoding, default None means utf-8.

        Returns
        -------
        list
            Two numpy arrays - one for the keys (object<str>) and one for the values (object<str> or float).
        """
        return self._gdxReadSymbol(gdx, symName, Mode.STRING, uelList, encoding)

    # @brief Reads symbol data from GDX into two numpy arrays, one for the keys (int) and one for the values (object<str> or float).
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
    # @param symName The name of the symbol to be read.
    # @param encoding The name of the encoding, default None means utf-8.
    # @return Two numpy arrays - one for the keys (int) and one for the values (object<str> or float).
    def gdxReadSymbolRaw(self, gdx, symName, encoding=None):
        """
        Reads symbol data from GDX into two numpy arrays, one for the keys (int) and one for the values (object<str> or float).

        Parameters
        ----------
        gdx : GDX handle
            GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
        symName : str
            The name of the symbol to be read.
        encoding : str, optional
            The name of the encoding, default None means utf-8.

        Returns
        -------
        list
            Two numpy arrays - one for the keys (int) and one for the values (object<str> or float).
        """
        return self._gdxReadSymbol(gdx, symName, Mode.RAW, encoding)

    # @brief Reads symbol data from GDX in a specific format that is well suited for creating a pandas.DataFrame with categoricals.
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
    # @param symName The name of the symbol to be read.
    # @param uelList List of UELs to be used for mapping internal numbers to labels, usually retrieved by 'gdxGetUelList'. If omitted, the UEL list is generated internally from the GDX file.
    #         Supplying this parameter can increase performance when reading multiple symbols from the same GDX file since the UEL list creation has to be performed only once.
    # @param encoding The name of the encoding, default None means utf-8.
    # @return Two numpy arrays and a list. The first array contains the keys (int) and the second one contains the values (object<str> or float). The list is two dimensional and contains a mapping for the integer keys to labels for each individual dimension.
    def gdxReadSymbolCat(self, gdx, symName, uelList=None, encoding=None):
        """
        Reads symbol data from GDX in a specific format that is well suited for creating a pandas.DataFrame with categoricals.

        Parameters
        ----------
        gdx : GDX handle
            GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
        symName : str
            The name of the symbol to be read.
        uelList : List[str], optional
            List of UELs to be used for mapping internal numbers to labels, usually retrieved by 'gdxGetUelList'. If omitted, the UEL list is generated internally from the GDX file.
            Supplying this parameter can increase performance when reading multiple symbols from the same GDX file since the UEL list creation has to be performed only once.
        encoding : str, optional
            The name of the encoding, default None means utf-8.

        Returns
        -------
        list
            Two numpy arrays and a list. The first array contains the keys (int) and the second one contains the values (object<str> or float).
            The list is two dimensional and contains a mapping for the integer keys to labels for each individual dimension.
        """
        return self._gdxReadSymbol(gdx, symName, Mode.CATEGORICAL, uelList, encoding)

    def _gdxWriteSymbol(
        self,
        gdx,
        symName,
        explText,
        dim,
        symType,
        subType,
        arrKeys,
        arrValues,
        mode,
        domains,
        relaxedType,
        majorList=None,
    ):
        if not isinstance(mode, Mode):
            raise Exception(
                "Unknown mode. Specify either Mode.RAW, Mode.STRING, Mode.MAP, or Mode.CATEGORICAL"
            )

        arrKeys, arrValues = self._convertNoneArrays(
            arrKeys, arrValues, symType, mode != Mode.STRING
        )

        self._validateKeyArray(arrKeys, dim)
        self._validateValueArray(arrValues, symType)
        if relaxedType:
            arrKeys = self._convertKeyTypes(arrKeys, mode != Mode.STRING)
            arrValues = self._convertValueTypes(arrValues, symType)
        self._validateTypes(arrKeys, arrValues, symType, mode != Mode.STRING)

        arrKeys, arrValues = self._convertMemoryLayouts(
            arrKeys, arrValues, mode, symType
        )

        if domains != None:
            if not isinstance(domains, list):
                raise Exception(
                    "Parameter domains has to be of type list, but is "
                    + str(type(domains))
                )
            if len(domains) != dim:
                raise Exception(
                    "Length of domains("
                    + str(len(domains))
                    + ") does not match parameter dim("
                    + str(dim)
                    + ")"
                )

        if isinstance(gdx, str):
            gdxHandle = new_gdxHandle_tp()
            rc, msg = gdxCreateD(gdxHandle, self._system_directory, GMS_SSSIZE)
            if not rc:
                raise Exception(msg)
            if not gdxOpenWrite(gdxHandle, gdx, "")[0]:
                raise Exception("Error opening GDX file " + gdx)
            ret = _gams2numpy.gdxWriteSymbol(
                gdxHandleToPtr(gdxHandle),
                symName,
                explText,
                dim,
                symType,
                subType,
                arrKeys,
                arrValues,
                majorList,
                mode.value,
                domains,
            )
            gdxClose(gdxHandle)
            gdxFree(gdxHandle)
            return ret
        return _gams2numpy.gdxWriteSymbol(
            gdxHandleToPtr(gdx),
            symName,
            explText,
            dim,
            symType,
            subType,
            arrKeys,
            arrValues,
            majorList,
            mode.value,
            domains,
        )

    # @brief Creates a GDX symbol and fills it with the data from the provided numpy arrays.
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
    # @param symName The name of the symbol to be created.
    # @param explText Explanatory text.
    # @param dim The dimension of the symbol.
    # @param symType The type of the symbol.
    # @param subType The sybType of the symbol.
    # @param arrKeys Two dimensional numpy array containing keys (object<str>).
    # @param arrValues Two dimensional numpy array containing values (object<str> or float).
    # @param domains List of domains (str) to be used for the symbol (optional).
    # @param relaxedType Automatically convert the columns of the numpy array into the required data types if possible (default: False).
    # @return None
    def gdxWriteSymbolStr(
        self,
        gdx,
        symName,
        explText,
        dim,
        symType,
        subType,
        arrKeys,
        arrValues,
        domains=None,
        relaxedType=False,
    ):
        """
        Creates a GDX symbol and fills it with the data from the provided numpy arrays

        Parameters
        ----------
        gdx : GDX handle
            GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name
        symName : str
            The name of the symbol to be created
        explText : str
            Explanatory text
        dim : int
            The dimension of the symbol
        symType : int
            The type of the symbol
        subType : int
            The sybType of the symbol
        domains : List[str], optional
            List of domains (str) to be used for the symbol (optional), by default None
        relaxedType : bool, optional
            Automatically convert the columns of the numpy array into the required data types if possible, by default False
        """
        return self._gdxWriteSymbol(
            gdx,
            symName,
            explText,
            dim,
            symType,
            subType,
            arrKeys,
            arrValues,
            Mode.STRING,
            domains,
            relaxedType,
        )

    # @brief Creates a GDX symbol and fills it with the data from the provided numpy arrays.
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
    # @param symName The name of the symbol to be created.
    # @param explText Explanatory text.
    # @param dim The dimension of the symbol.
    # @param symType The type of the symbol.
    # @param subType The sybType of the symbol.
    # @param arrKeys Two dimensional numpy array containing for keys (int).
    # @param arrValues Two dimensional numpy array containing values (object<str> or float).
    # @param domains List of domains (str) to be used for the symbol (optional).
    # @param relaxedType Automatically convert the columns of the numpy array into the required data types if possible (default: False).
    # @return None
    def gdxWriteSymbolRaw(
        self,
        gdx,
        symName,
        explText,
        dim,
        symType,
        subType,
        arrKeys,
        arrValues,
        domains=None,
        relaxedType=False,
    ):
        """
        Creates a GDX symbol and fills it with the data from the provided numpy arrays.

        Parameters
        ----------
        gdx : GDX handle | str
            GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
        symName : str
            The name of the symbol to be created.
        explText : str
            Explanatory text.
        dim : int
            The dimension of the symbol.
        symType : int
            The type of the symbol.
        subType : int
            The sybType of the symbol.
        arrKeys : ndarray
            Two dimensional numpy array containing for keys (int).
        arrValues : ndarray
            Two dimensional numpy array containing values (object<str> or float).
        domains : List[str], optional
            List of domains (str) to be used for the symbol, by default None
        relaxedType : bool, optional
            Automatically convert the columns of the numpy array into the required data types if possible (default: False).

        Returns
        -------
        None
        """
        return self._gdxWriteSymbol(
            gdx,
            symName,
            explText,
            dim,
            symType,
            subType,
            arrKeys,
            arrValues,
            Mode.RAW,
            domains,
            relaxedType,
        )

    # @brief Creates a GDX symbol and fills it with the data from the provided numpy arrays in map mode.
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
    # @param symName The name of the symbol to be created.
    # @param explText Explanatory text.
    # @param dim The dimension of the symbol.
    # @param symType The type of the symbol.
    # @param subType The sybType of the symbol.
    # @param arrKeys Two dimensional numpy array containing keys (int).
    # @param arrValues Two dimensional numpy array containing values (object<str> or float).
    # @param domains List of domains (str) to be used for the symbol (optional).
    # @param relaxedType Automatically convert the columns of the numpy array into the required data types if possible (default: False).
    # @return None
    def gdxWriteSymbolMap(
        self,
        gdx,
        symName,
        explText,
        dim,
        symType,
        subType,
        arrKeys,
        arrValues,
        domains=None,
        relaxedType=False,
    ):
        """
        Creates a GDX symbol and fills it with the data from the provided numpy arrays in map mode.

        Parameters
        ----------
        gdx : GDX handle | str
            GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
        symName : str
            The name of the symbol to be created.
        explText : str
            Explanatory text.
        dim : int
            The dimension of the symbol.
        symType : int
            The type of the symbol.
        subType : int
            The sybType of the symbol.
        arrKeys : ndarray
            Two dimensional numpy array containing keys (int).
        arrValues : ndarray
            Two dimensional numpy array containing values (object<str> or float).
        domains : List[str], optional
            List of domains (str) to be used for the symbol, by default None
        relaxedType : bool, optional
            Automatically convert the columns of the numpy array into the required data types if possible (default: False).

        Returns
        -------
        None
        """
        return self._gdxWriteSymbol(
            gdx,
            symName,
            explText,
            dim,
            symType,
            subType,
            arrKeys,
            arrValues,
            Mode.MAP,
            domains,
            relaxedType,
        )

    # @brief Creates a GDX symbol and fills it with data from the provided numpy arrays usually derived from a pandas.Dataframe with categoricals. Since UELs have to be registred manually before, this method can be used with a GDX handle only.
    # @param gdx GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
    # @param symName The name of the symbol to be created.
    # @param explText Explanatory text.
    # @param dim The dimension of the symbol.
    # @param symType The type of the symbol.
    # @param subType The sybType of the symbol.
    # @param arrKeys Two dimensional numpy array containing for keys (int).
    # @param arrValues Two dimensional numpy array containing values (object<str> or float).
    # @param majorList A two dimensional list containing a mapping for the integer keys to labels for each individual dimension.
    # @param domains List of domains (str) to be used for the symbol (optional).
    # @param relaxedType Automatically convert the columns of the numpy array into the required data types if possible (default: False).
    # @return None
    def gdxWriteSymbolCat(
        self,
        gdx,
        symName,
        explText,
        dim,
        symType,
        subType,
        arrKeys,
        arrValues,
        majorList,
        domains=None,
        relaxedType=False,
    ):
        """
        Creates a GDX symbol and fills it with data from the provided numpy arrays usually derived from a pandas.Dataframe with categoricals. Since UELs have to be registred manually before, this method can be used with a GDX handle only.

        Parameters
        ----------
        gdx : GDX handle | str
            GDX handle created with 'gdxcc.new_gdxHandle_tp' or GDX file name.
        symName : str
            The name of the symbol to be created.
        explText : str
            Explanatory text.
        dim : int
            The dimension of the symbol.
        symType : int
            The type of the symbol.
        subType : int
            The sybType of the symbol.
        arrKeys : ndarray
            Two dimensional numpy array containing for keys (int).
        arrValues : ndarray
            Two dimensional numpy array containing values (object<str> or float).
        majorList : list
            A two dimensional list containing a mapping for the integer keys to labels for each individual dimension.
        domains : List[str], optional
            List of domains (str) to be used for the symbol, by default None
        relaxedType : bool, optional
            Automatically convert the columns of the numpy array into the required data types if possible (default: False).

        Returns
        -------
        None
        """
        return self._gdxWriteSymbol(
            gdx,
            symName,
            explText,
            dim,
            symType,
            subType,
            arrKeys,
            arrValues,
            Mode.CATEGORICAL,
            domains,
            relaxedType,
            majorList,
        )

    def _gmdReadSymbol(self, gmd, symName, mode, uelList=None, encoding=None):
        if not isinstance(mode, Mode):
            raise Exception(
                "Unknown mode. Specify either Mode.RAW, Mode.STRING, or Mode.CATEGORICAL."
            )

        if isinstance(gmd, GamsDatabase):
            gmdH = gmd._gmd
        else:
            gmdH = gmd
        return _gams2numpy.gmdReadSymbol(
            gmdHandleToPtr(gmdH), symName, mode.value, uelList, encoding
        )

    # @brief Reads symbol data from GMD into two numpy arrays, one for keys (object<str>) and one for values (object<str> or float).
    # @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
    # @param symName The name of the symbol to be read.
    # @param uelList List of UELs to be used for mapping internal numbers to labels, usually retrieved by 'gmdGetUelList'. If omitted, the UEL list is generated internally from the GMD handle.
    #         Supplying this parameter can increase performance when reading multiple symbols from the same GMD handle since the UEL list creation has to be performed only once.
    # @param encoding The name of the encoding, default None means utf-8.
    # @return Two numpy arrays - one for the keys (object<str>) and one for the values (object<str> or float).
    def gmdReadSymbolStr(self, gmd, symName, uelList=None, encoding=None):
        """
        Reads symbol data from GMD into two numpy arrays, one for keys (object<str>) and one for values (object<str> or float).

        Parameters
        ----------
        gmd : GMD handle
            GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase
        symName : str
            The name of the symbol to be read
        uelList : List[str], optional
            List of UELs to be used for mapping internal numbers to labels, usually retrieved by 'gmdGetUelList'. If omitted, the UEL list is generated internally from the GMD handle
            Supplying this parameter can increase performance when reading multiple symbols from the same GMD handle since the UEL list creation has to be performed only once
        encoding : str, optional
            The name of the encoding, default None means utf-8

        Returns
        -------
        list
            Two numpy arrays - one for the keys (object<str>) and one for the values (object<str> or float)
        """
        return self._gmdReadSymbol(gmd, symName, Mode.STRING, uelList, encoding)

    # @brief Reads symbol data from GMD  into two numpy arrays, one for keys (int) and one for values (object<str> or float).
    # @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
    # @param symName The name of the symbol to be read.
    # @param encoding The name of the encoding, default None means utf-8.
    # @return Two numpy arrays - one for the keys (int) and one for the values (object<str> or float).
    def gmdReadSymbolRaw(self, gmd, symName, encoding=None):
        """
        Reads symbol data from GMD  into two numpy arrays, one for keys (int) and one for values (object<str> or float)

        Parameters
        ----------
        gmd : GMD handle
            GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase
        symName : str
            The name of the symbol to be read
        encoding : str, optional
            The name of the encoding, default None means utf-8

        Returns
        -------
        list
            Two numpy arrays - one for the keys (int) and one for the values (object<str> or float)
        """
        return self._gmdReadSymbol(gmd, symName, Mode.RAW, encoding)

    # @brief Reads symbol data from GMD in a specific format that is well suited for creating a pandas.Dataframe with categoricals.
    # @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
    # @param symName The name of the symbol to be read.
    # @param encoding The name of the encoding, default None means utf-8.
    # @return Two numpy arrays and a list. The first array contains the keys (int) and the second one contains the values (object<str> or float). The list is two dimensional and contains a mapping for the integer keys to labels for each individual dimension.
    def gmdReadSymbolCat(self, gmd, symName, uelList=None, encoding=None):
        """
        Reads symbol data from GMD in a specific format that is well suited for creating a pandas.Dataframe with categoricals.

        Parameters
        ----------
        gmd : GMD handle
            GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase
        symName : str
            The name of the symbol to be read
        encoding : str, optional
            The name of the encoding, default None means utf-8

        Returns
        -------
        Two numpy arrays and a list. The first array contains the keys (int) and the second one contains the values (object<str> or float).
        The list is two dimensional and contains a mapping for the integer keys to labels for each individual dimension.
        """
        return self._gmdReadSymbol(gmd, symName, Mode.CATEGORICAL, uelList, encoding)

    def _gmdFillSymbol(self, gmd, symbolPtr, arrKeys, arrValues, mode, merge, relaxedType, checkUel, majorList=None, epsToZero=True):
        if not isinstance(mode, Mode) or mode not in [Mode.RAW, Mode.STRING, Mode.CATEGORICAL]:
            raise Exception("Unknown mode. Specify either Mode.RAW, Mode.STRING, or Mode.CATEGORICAL")

        if isinstance(gmd, GamsDatabase):
            gmdH = gmd._gmd
        else:
            gmdH = gmd
        if isinstance(symbolPtr, _GamsSymbol):
            symPtr = symbolPtr._sym_ptr
        else:
            symPtr = symbolPtr

        symType = gmdSymbolType(gmdH, symPtr)[1]
        symDim = gmdSymbolDim(gmdH, symPtr)[1]

        arrKeys, arrValues = self._convertNoneArrays(arrKeys, arrValues, symType, mode!=Mode.STRING)

        self._validateKeyArray(arrKeys, symDim)
        self._validateValueArray(arrValues, symType)
        if relaxedType:
            arrKeys = self._convertKeyTypes(arrKeys, mode!=Mode.STRING)
            arrValues = self._convertValueTypes(arrValues, symType)
        self._validateTypes(arrKeys, arrValues, symType, mode!=Mode.STRING)

        return _gams2numpy.gmdFillSymbol(gmdHandleToPtr(gmdH), symPtr, arrKeys, arrValues, majorList, mode.value, merge, checkUel, epsToZero)

    # @brief Fills an existing GMD symbol with the data from the provided numpy arrays.
    # @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
    # @param symbolPtr GMD symbol pointer or an instance of GamsParamater, GamsSet, GamsVariable or GamsEquation.
    # @param arrKeys Two dimensional numpy array containing keys (object<str>).
    # @param arrValues Two dimensional numpy array containing values (object<str> or float).
    # @param merge Allow to write to a symbol that already contains data. In case of duplicate records, the last record will overwrite all previous ones (default: False).
    # @param relaxedType Automatically convert the columns of the numpy array into the required data types if possible (default: False).
    # @param epsToZero Automatically convert any -0.0 to 0.0 in the records.
    # @return None
    def gmdFillSymbolStr(self, gmd, symbolPtr, arrKeys: np.ndarray, arrValues: np.ndarray, merge: bool = False, relaxedType: bool = False, epsToZero: bool = True):
        """
        Fills an existing GMD symbol with the data from the provided numpy arrays

        Parameters
        ----------
        gmd : GMD handle | GamsDatabase
            GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
        symbolPtr : GamsParamater | GamsSet | GamsVariable | GamsEquation
            GMD symbol pointer or an instance of GamsParamater, GamsSet, GamsVariable or GamsEquation.
        arrKeys : ndarray
            Two dimensional numpy array containing keys (object<str>).
        arrValues : ndarray
            Two dimensional numpy array containing values (object<str> or float).
        merge : bool, optional
            Allow to write to a symbol that already contains data. In case of duplicate records, the last record will overwrite all previous ones (default: False).
        relaxedType : bool, optional
            Automatically convert the columns of the numpy array into the required data types if possible (default: False).
        epsToZero : bool, optional
            Automatically convert any -0.0 to 0.0 in the records.

        Returns
        -------
        None
            None
        """
        return self._gmdFillSymbol(gmd, symbolPtr, arrKeys, arrValues, Mode.STRING, merge, relaxedType, True, epsToZero=epsToZero)


    # @brief Fills an existing GMD symbol with the data from the provided numpy arrays.
    # @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
    # @param symbolPtr GMD symbol pointer or an instance of GamsParamater, GamsSet, GamsVariable or GamsEquation.
    # @param arrKeys Two dimensional numpy array containing keys (int).
    # @param arrValues Two dimensional numpy array containing values (object<str> or float).
    # @param merge Allow to write to a symbol that already contains data. In case of duplicate records, the last record will overwrite all previous ones (default: False).
    # @param relaxedType Automatically convert the columns of the numpy array into the required data types if possible (default: False).
    # @param checkUel Enable or disable validity checks for UELs. Setting this to False can slightly improve performance (default: True).
    # @param epsToZero Automatically convert any -0.0 to 0.0 in the records.
    # @return None
    def gmdFillSymbolRaw(
        self,
        gmd,
        symbolPtr,
        arrKeys: np.ndarray,
        arrValues: np.ndarray,
        merge: bool = False,
        relaxedType: bool = False,
        checkUel: bool = True,
        epsToZero: bool = True
    ):
        """
        Fills an existing GMD symbol with the data from the provided numpy arrays

        Parameters
        ----------
        gmd : GMD handle | GamsDatabase
            GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
        symbolPtr : GamsParamater | GamsSet | GamsVariable | GamsEquation
            GMD symbol pointer or an instance of GamsParamater, GamsSet, GamsVariable or GamsEquation.
        arrKeys : ndarray
            Two dimensional numpy array containing keys (int).
        arrValues : ndarray
            Two dimensional numpy array containing values (object<str> or float).
        merge : bool, optional
            Allow to write to a symbol that already contains data. In case of duplicate records, the last record will overwrite all previous ones (default: False).
        relaxedType : bool, optional
            Automatically convert the columns of the numpy array into the required data types if possible (default: False).
        checkUel : bool, optional
            Enable or disable validity checks for UELs. Setting this to False can slightly improve performance (default: True).
        epsToZero : bool, optional
            Automatically convert any -0.0 to 0.0 in the records.
            
        Returns
        -------
        None
            None
        """
        return self._gmdFillSymbol(gmd, symbolPtr, arrKeys, arrValues, Mode.RAW, merge, relaxedType, checkUel, epsToZero=epsToZero)


    # @brief Fills an existing GMD symbol with the data from the provided numpy arrays usually derived from a pandas.Dataframe with categoricals. UELs have to be registered manually before.
    # @param gmd GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
    # @param symbolPtr GMD symbol pointer or an instance of GamsParamater, GamsSet, GamsVariable or GamsEquation.
    # @param arrKeys Two dimensional numpy array containing keys (int).
    # @param arrValues Two dimensional numpy array containing values (object<str> or float).
    # @param majorList A two dimensional list containing a mapping for the integer keys to labels for each individual dimension.
    # @param merge Allow to write to a symbol that already contains data. In case of duplicate records, the last record will overwrite all previous ones (default: False).
    # @param relaxedType Automatically convert the columns of the numpy array into the required data types if possible (default: False).
    # @param checkUel Enable or disable validity checks for UELs. Setting this to False can slightly improve performance (default: True).
    # @param epsToZero Automatically convert any -0.0 to 0.0 in the records.
    # @return None
    def gmdFillSymbolCat(
        self,
        gmd,
        symbolPtr,
        arrKeys: np.ndarray,
        arrValues: np.ndarray,
        majorList: list,
        merge: bool = False,
        relaxedType: bool = False,
        checkUel: bool = True,
        epsToZero: bool = True
    ):
        """
        Fills an existing GMD symbol with the data from the provided numpy arrays usually derived from a pandas.Dataframe with categoricals. UELs have to be registered manually before.

        Parameters
        ----------
        gmd : GMD handle | GamsDatabase
            GMD handle created with 'gmdcc.new_gmdHandle_tp' or an instance of GamsDatabase.
        symbolPtr : GamsParamater | GamsSet | GamsVariable | GamsEquation
            GMD symbol pointer or an instance of GamsParamater, GamsSet, GamsVariable or GamsEquation.
        arrKeys : ndarray
            Two dimensional numpy array containing keys (int).
        arrValues : ndarray
            Two dimensional numpy array containing values (object<str> or float).
        majorList : list
            A two dimensional list containing a mapping for the integer keys to labels for each individual dimension.
        merge : bool, optional
            Allow to write to a symbol that already contains data. In case of duplicate records, the last record will overwrite all previous ones (default: False).
        relaxedType : bool, optional
            Automatically convert the columns of the numpy array into the required data types if possible (default: False).
        checkUel : bool, optional
            Enable or disable validity checks for UELs. Setting this to False can slightly improve performance (default: True).
        epsToZero : bool, optional
            Automatically convert any -0.0 to 0.0 in the records.
            
        Returns
        -------
        None
        """
        return self._gmdFillSymbol(gmd, symbolPtr, arrKeys, arrValues, Mode.CATEGORICAL, merge, relaxedType, checkUel, majorList, epsToZero)
