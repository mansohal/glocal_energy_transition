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

import os
import copy
from typing import TYPE_CHECKING, Sequence, Any, Union, List
from warnings import warn
import pandas as pd
import numpy as np
from gams.core import gdx
import gams.transfer._abcs as abcs
from gams.transfer.syms import (
    Set,
    Parameter,
    Variable,
    Equation,
    Alias,
    UniverseAlias,
)


from gams.transfer._internals import (
    SpecialValues,
    DomainStatus,
    convert_to_categoricals_cat,
    convert_to_categoricals_str,
    generate_unique_labels,
    get_keys_and_values,
    GAMS_VARIABLE_SUBTYPES,
    GAMS_EQUATION_SUBTYPES,
    GAMS_DOMAIN_STATUS,
)

if TYPE_CHECKING:
    from gams.transfer.containers import Container


def isin(element: Any, container: Sequence) -> bool:
    """
    Checks if an element is in a sequence.

    Parameters
    ----------
    element: Any
        The element to search for.
    container: Sequence
        The sequence where the element is to be searched in.

    Returns
    -------
    bool
        True if the element is in the container; False otherwise.
    """
    for item in container:
        if element is item:
            return True
    return False


def container_read(
    container: "Container",
    load_from: Union[str, os.PathLike],
    symbols: Union[None, str, List[str]],
    records: bool,
    mode: str,
    encoding: Union[None, str],
) -> None:
    """
    Read symbols and associated data from a GDX file into a Container.

    This function reads symbols and their associated data from a GDX (GAMS Data Exchange) file into a Container object.
    You can specify the symbols to read, whether to read associated records, the reading mode, and encoding if required.

    Parameters
    ----------
    container : Container
        The target Container where symbols and data will be read into.
    load_from : str | Path
        The path to the GDX file from which to read symbols and data.
    symbols : None | str | List[str]
        A list of symbol names to read from the GDX file. If None, all symbols will be read.
    records : bool
        A flag indicating whether to read associated data records for symbols.
    mode : str
        The reading mode for the symbols. Use 'category' for categorical symbols or 'string' for string symbols.
    encoding : None | str
        The encoding to use when reading symbols from the GDX file. Default is None.

    Raises
    ------
    Exception
        If there are issues with loading the GDX DLL or handling symbol metadata perhaps due to wrong path.
    Exception
        If the code tries to add an existing symbol.
    Exception
        Not being able to read a symbol in a specific mode.
    ValueError
        If an unrecognized reading mode is provided.
    """
    if len(container) == 0:
        initially_empty_container = True
    else:
        initially_empty_container = False

    # test dll connection and create gdxhandle
    try:
        gdxHandle = gdx.new_gdxHandle_tp()
        rc = gdx.gdxCreateD(gdxHandle, container.system_directory, gdx.GMS_SSSIZE)
        assert rc[0], rc[1]

        ret, fileVersion, producer = gdx.gdxFileVersion(gdxHandle)

    except:
        raise Exception("Could not properly load GDX DLL, check system_directory path")

    try:

        # open file for reading
        rc = gdx.gdxOpenRead(gdxHandle, load_from)
        assert rc
        ret, symCount, _ = gdx.gdxSystemInfo(gdxHandle)

        # setting special values
        specVals = gdx.doubleArray(gdx.GMS_SVIDX_MAX)
        specVals[gdx.GMS_SVIDX_UNDEF] = SpecialValues.UNDEF
        specVals[gdx.GMS_SVIDX_NA] = SpecialValues.NA
        specVals[gdx.GMS_SVIDX_EPS] = SpecialValues.EPS
        specVals[gdx.GMS_SVIDX_PINF] = SpecialValues.POSINF
        specVals[gdx.GMS_SVIDX_MINF] = SpecialValues.NEGINF

        rc = gdx.gdxSetSpecialValues(gdxHandle, specVals)
        assert rc

        # check for acronyms
        n_acronyms = gdx.gdxAcronymCount(gdxHandle)
        if n_acronyms > 0:
            warn(
                "GDX file contains acronyms. "
                "Acronyms are not supported and are set to GAMS NA."
            )

        acronyms = []
        for i in range(n_acronyms):
            ret, acr_name, acr_text, acr_idx = gdx.gdxAcronymGetInfo(gdxHandle, i + 1)
            acronyms.append(acr_idx)

        # find symbol metadata if not reading in all
        read_all_symbols = True
        SYMBOL_METADATA = []
        LINK_DOMAINS = []
        SYMBOLS_W_RECORDS = []

        if symbols is not None:
            read_all_symbols = False
            SYMBOL_METADATA = gdx_get_metadata_by_names(
                container, gdxHandle, symbols, encoding
            )

            # sort symbols by gdx number in order to read symbols in gdx order not user order
            SYMBOL_METADATA = sorted(
                SYMBOL_METADATA, key=lambda x: x["gdx_symbol_number"]
            )

        # two paths to creating symbol objects
        if read_all_symbols:
            #
            #
            # fastpath if reading in all symbols (by number)
            for i in range(1, symCount + 1):
                md = gdx_get_metadata_by_number(container, gdxHandle, i, encoding)

                # capture metadata
                SYMBOL_METADATA.append(md)

                # check if symbol already exists in container
                if not initially_empty_container:
                    if md["name"] in container:
                        raise Exception(
                            f"Attempting to create a new symbol (through a read operation) named `{md['name']}` "
                            "but an object with this name already exists in the Container. "
                            "Symbol replacement is only possible if the existing symbol is "
                            "first removed from the Container with the `<container>.removeSymbols()` method."
                        )

                # figure out domain status
                if GAMS_DOMAIN_STATUS.get(md["domain_type"], None) == "regular":
                    LINK_DOMAINS.append(md)

                # capture symbols that have records (not aliases)
                if md["number_records"] > 0 and md["type"] != gdx.GMS_DT_ALIAS:
                    SYMBOLS_W_RECORDS.append(md)

                # create the symbol object in the container
                create_symbol_from_metadata(container, md)

        else:
            #
            #
            # other

            for md in SYMBOL_METADATA:
                # check if symbol already exists in container
                if not initially_empty_container:
                    if md["name"] in container:
                        raise Exception(
                            f"Attempting to create a new symbol (through a read operation) named `{md['name']}` "
                            "but an object with this name already exists in the Container. "
                            "Symbol replacement is only possible if the existing symbol is "
                            "first removed from the Container with the `<container>.removeSymbols()` method."
                        )

                if GAMS_DOMAIN_STATUS.get(md["domain_type"], None) == "regular":
                    LINK_DOMAINS.append(md)

                # capture symbols that have records (not aliases)
                if md["number_records"] > 0 and md["type"] != gdx.GMS_DT_ALIAS:
                    SYMBOLS_W_RECORDS.append(md)

                # create the symbol object in the container
                create_symbol_from_metadata(container, md)

        #
        #
        # link domain objects
        READ_SYMBOLS = [md["name"] for md in SYMBOL_METADATA]
        for md in LINK_DOMAINS:
            domain = md["domain"]
            for n, i in enumerate(domain):
                if i != "*" and i in READ_SYMBOLS:
                    domain[n] = container[i]

            container[md["name"]]._domain = domain

        #
        #
        # main records read
        if records:
            # get and store GDX_UELS
            GDX_UELS = container._gams2np.gdxGetUelList(gdxHandle, encoding=encoding)
            GDX_UELS[0] = "*"

            for md in SYMBOLS_W_RECORDS:
                # get symbol object
                symobj = container[md["name"]]

                # fastpath for scalar symbols
                if md["dimension"] == 0 and md["number_records"] == 1:
                    ret, nrRecs = gdx.gdxDataReadRawStart(
                        gdxHandle, md["gdx_symbol_number"]
                    )
                    ret, keys, vals, a = gdx.gdxDataReadRaw(gdxHandle)
                    ret = gdx.gdxDataReadDone(gdxHandle)

                    symobj._records = pd.DataFrame(
                        [vals[: len(symobj._attributes)]],
                        columns=symobj._attributes,
                        dtype=float,
                    )

                else:
                    if mode.casefold() == "category":
                        try:
                            (
                                arrkeys,
                                arrvals,
                                unique_uels,
                            ) = container._gams2np.gdxReadSymbolCat(
                                gdxHandle, md["name"], GDX_UELS, encoding=encoding
                            )
                        except:
                            raise Exception(
                                f"Could not properly read symbol {md['name']} from GDX file. "
                                "Try setting read argument mode='string'"
                            )

                        # convert to categorical dataframe (return None if no data)
                        df = convert_to_categoricals_cat(arrkeys, arrvals, unique_uels)

                    elif mode.casefold() == "string":
                        try:
                            arrkeys, arrvals = container._gams2np.gdxReadSymbolStr(
                                gdxHandle, md["name"], GDX_UELS, encoding=encoding
                            )
                        except:
                            raise Exception(
                                f"Could not properly read symbol {md['name']} from GDX file."
                            )

                        # convert to categorical dataframe (return None if no data)
                        df = convert_to_categoricals_str(arrkeys, arrvals, GDX_UELS[1:])

                    else:
                        raise ValueError("Unrecognized read `mode`")

                    # set records
                    symobj._records = df

                    # set column names
                    symobj._records.columns = (
                        generate_unique_labels(symobj.domain_names) + symobj._attributes
                    )

                # remap any acronyms to SpecialValues.NA
                if len(acronyms) != 0:
                    if isinstance(
                        symobj, (abcs.ABCParameter, abcs.ABCVariable, abcs.ABCEquation)
                    ):
                        for x in range(len(symobj._records.columns)):
                            if x >= symobj.dimension:
                                for a in acronyms:
                                    idx = symobj._records.iloc[:, x][
                                        symobj._records.iloc[:, x] == a * 1e301
                                    ].index
                                    symobj._records.iloc[idx, x] = SpecialValues.NA
    except Exception as err:

        # close file
        gdx.gdxClose(gdxHandle)
        gdx.gdxFree(gdxHandle)
        gdx.gdxLibraryUnload()

        raise err

    # close file
    gdx.gdxClose(gdxHandle)
    gdx.gdxFree(gdxHandle)
    gdx.gdxLibraryUnload()


def create_symbol_from_metadata(container: "Container", metadata: dict) -> None:
    """
    Create a symbol object in the specified Container based on provided metadata.

    This function creates a symbol object in the given Container based on the provided metadata.
    The metadata includes information such as the symbol type, domain, description, and more.

    Parameters
    ----------
    container : Container
        The Container where the symbol object will be created.
    metadata : dict
        Metadata containing information about the symbol to be created. It should include:
        - 'name': The name of the symbol.
        - 'type': The GAMS type of the symbol (e.g., gdx.GMS_DT_SET, gdx.GMS_DT_PAR, gdx.GMS_DT_VAR, gdx.GMS_DT_EQU, gdx.GMS_DT_ALIAS).
        - 'userinfo': The GAMS userinfo of the symbol (subtype).
        - 'domain': The domain associated with the symbol.
        - 'description': The description or documentation for the symbol.

    Raises
    ------
    Exception
        If the provided metadata indicates an unknown GDX symbol classification.
    """
    if metadata["type"] == gdx.GMS_DT_ALIAS:
        # test for universe alias
        if metadata["userinfo"] != 0:
            try:
                Alias._from_gams(
                    container, metadata["name"], container.data[metadata["parent_set"]]
                )
            except Exception as err:
                raise Exception(
                    (
                        f"Cannot create the Alias symbol `{metadata['name']}` "
                        f"because the parent set (`{metadata['parent_set']}`) is not "
                        "being read into the in the Container. "
                        "Alias symbols require the parent set object to exist in the Container. "
                        f"Add `{metadata['parent_set']}` to the list of symbols to read."
                    )
                )
        else:
            UniverseAlias._from_gams(container, metadata["name"])

    # regular set
    elif metadata["type"] == gdx.GMS_DT_SET and metadata["userinfo"] == 0:
        Set._from_gams(
            container,
            metadata["name"],
            metadata["domain"],
            is_singleton=False,
            description=metadata["description"],
        )

    # singleton set
    elif metadata["type"] == gdx.GMS_DT_SET and metadata["userinfo"] == 1:
        Set._from_gams(
            container,
            metadata["name"],
            metadata["domain"],
            is_singleton=True,
            description=metadata["description"],
        )

    # parameters
    elif metadata["type"] == gdx.GMS_DT_PAR:
        Parameter._from_gams(
            container,
            metadata["name"],
            metadata["domain"],
            description=metadata["description"],
        )

    # variables
    elif metadata["type"] == gdx.GMS_DT_VAR:
        Variable._from_gams(
            container,
            metadata["name"],
            GAMS_VARIABLE_SUBTYPES.get(metadata["userinfo"], "free"),
            metadata["domain"],
            description=metadata["description"],
        )

    # equations
    elif metadata["type"] == gdx.GMS_DT_EQU:
        Equation._from_gams(
            container,
            metadata["name"],
            GAMS_EQUATION_SUBTYPES.get(metadata["userinfo"], "eq"),
            metadata["domain"],
            description=metadata["description"],
        )

    # unknown symbols
    else:
        raise Exception(
            f"Unknown GDX symbol classification (GAMS Type= {metadata['type']}, "
            f"GAMS Subtype= {metadata['userinfo']}). ",
            f"Cannot load symbol `{metadata['name']}`",
        )


def gdx_get_metadata_by_number(
    container: "Container", gdxHandle, symbol_number: int, encoding: Union[None, str]
) -> dict:
    """
    Retrieve metadata for a GDX symbol by its symbol number.

    This function retrieves metadata for a GDX symbol in a Container by specifying its symbol number.

    Parameters
    ----------
    container : Container
        The Container where the symbol is located.

    gdxHandle : gdx.new_gdxHandle_tp()
        The GDX handle or path to the GDX file where the symbol is stored.

    symbol_number : int
        The symbol number of the GDX symbol for which metadata is to be retrieved.

    encoding : None | str
        The encoding to use when reading symbols from the GDX file. Default is None.

    Returns
    -------
    dict
        A dictionary containing metadata for the GDX symbol.
    """
    ret, syid, dimen, typ = gdx.gdxSymbolInfo(gdxHandle, symbol_number)
    synr, nrecs, userinfo, _ = gdx.gdxSymbolInfoX(gdxHandle, symbol_number)
    domain_type, domain = gdx.gdxSymbolGetDomainX(gdxHandle, symbol_number)
    expltxt = container._gams2np._gdxGetSymbolExplTxt(
        gdxHandle, symbol_number, encoding=encoding
    )

    # gdx specific adjustment for equations
    if typ == gdx.GMS_DT_EQU:
        userinfo = userinfo - gdx.GMS_EQU_USERINFO_BASE

    if typ == gdx.GMS_DT_ALIAS:
        _, parent_set, _, _ = gdx.gdxSymbolInfo(gdxHandle, userinfo)
    else:
        parent_set = None

    # special handling of i(i) -- convert to relaxed domain_type
    if dimen == 1:
        if syid == domain[0]:
            domain_type = 2

    return {
        "name": syid,
        "gdx_symbol_number": symbol_number,
        "dimension": dimen,
        "type": typ,
        "userinfo": userinfo,
        "number_records": nrecs,
        "description": expltxt,
        "domain_type": domain_type,
        "domain": domain,
        "parent_set": parent_set,
    }


def gdx_get_metadata_by_names(
    container: "Container",
    gdxHandle,
    symbol_names: Union[str, List[str]],
    encoding: Union[None, str],
) -> List[dict]:
    """
    Retrieve metadata for GDX symbols by their names.

    This function retrieves metadata for one or more GDX symbols in a Container based on their names.

    Parameters
    ----------
    container: Container
        The Container where the symbols are located.

    gdxHandle: gdx.new_gdxHandle_tp()
        The GDX handle or path to the GDX file where the symbols are stored.

    symbol_names: str | List[str]
        The name or list of names of the GDX symbols for which metadata is to be retrieved.

    encoding: None | str
        The encoding used to decode the symbol descriptions. If None, default encoding is used.

    Returns
    -------
    List[dict]
        A list of dictionaries, each containing metadata for a GDX symbol.

    Raises
    ------
    ValueError
        If symbol does not exist

    Notes
    -----
    - This function is typically used during the process of reading symbols from a GDX file.
    - It retrieves metadata for one or more GDX symbols identified by their names.
    - The retrieved metadata provides information about the symbols' attributes and domains.
    """
    if isinstance(symbol_names, str):
        symbol_names = [symbol_names]

    metadata = []
    for sym in symbol_names:
        ret, symnr = gdx.gdxFindSymbol(gdxHandle, sym)
        if symnr == -1:
            raise ValueError(
                f"User specified to read symbol `{sym}`, "
                "but it does not exist in the GDX file."
            )

        ret, syid, dimen, typ = gdx.gdxSymbolInfo(gdxHandle, symnr)
        synr, nrecs, userinfo, _ = gdx.gdxSymbolInfoX(gdxHandle, symnr)
        domain_type, domain = gdx.gdxSymbolGetDomainX(gdxHandle, symnr)
        expltxt = container._gams2np._gdxGetSymbolExplTxt(
            gdxHandle, symnr, encoding=encoding
        )

        # gdx specific adjustment for equations
        if typ == gdx.GMS_DT_EQU:
            userinfo = userinfo - gdx.GMS_EQU_USERINFO_BASE

        if typ == gdx.GMS_DT_ALIAS:
            _, parent_set, _, _ = gdx.gdxSymbolInfo(gdxHandle, userinfo)
        else:
            parent_set = None

        # special handling of i(i) -- convert to relaxed domain_type
        if dimen == 1:
            if syid == domain[0]:
                domain_type = 2

        metadata.append(
            {
                "name": syid,
                "gdx_symbol_number": symnr,
                "dimension": dimen,
                "type": typ,
                "userinfo": userinfo,
                "number_records": nrecs,
                "description": expltxt,
                "domain_type": domain_type,
                "domain": domain,
                "parent_set": parent_set,
            }
        )

    return metadata


def container_write(
    container: "Container",
    write_to: Union[str, os.PathLike],
    symbols: Union[None, Sequence],
    uel_priority: Union[None, Sequence],
    compress: bool,
    mode: str,
    eps_to_zero: bool,
) -> None:
    """
    Write data from a Container to a GDX (GAMS Data Exchange) file.

    This function writes data from a Container to a GDX file. The GDX file can store symbols, sets, parameters,
    variables, and equations. You can specify which symbols to write, set the UEL (Unique Element Label) priority,
    enable compression, and choose the writing mode (category or string).

    Parameters
    ----------
    container: Container
        The Container containing the data to be written.

    write_to: str | Path
        The path to the GDX file where the data will be written.

    symbols: None | Sequence
        A list of symbols to write to the GDX file. If None, all symbols in the container will be written.

    uel_priority: None | Sequence
        A list of UELs (Unique Element Labels) to be given priority during writing. These UELs will be written first.

    compress: bool
        If True, enable compression for the GDX file.

    mode: str
        The writing mode for symbols. Choose between "category" or "string" mode. In "category" mode, symbols are
        written as categorical data, while in "string" mode, symbols are written as strings.
    """
    if symbols is None:
        write_all_symbols = True
    else:
        write_all_symbols = False

    if write_all_symbols:
        symbols = container.listSymbols()

    # reorder symbols if necessary
    if container._isValidSymbolOrder() == False:
        container.reorderSymbols()

    # get symbol objects to write
    symobjs = container.getSymbols(symbols)
    symnames = [sym.name for sym in symobjs]

    # assert valid records
    container._assert_valid_records(symbols=symbols)

    # check symbols
    for symobj in symobjs:
        if not symobj.isValid():
            raise Exception(
                f"Cannot write to GDX because symbol `{symobj.name}` is invalid. "
                "Use `<symbol>.isValid(verbose=True)` to debug."
            )

    # create gdxHandle
    gdxHandle = gdx.new_gdxHandle_tp()
    rc, msg = gdx.gdxCreateD(gdxHandle, container.system_directory, gdx.GMS_SSSIZE)
    if not rc:
        raise Exception(msg)

    try:

        # open GDX for writing
        if compress == False:
            if not gdx.gdxOpenWrite(gdxHandle, write_to, "GAMS Transfer")[0]:
                raise Exception(f"Error opening GDX `{write_to}` for writing")
        else:
            if not gdx.gdxOpenWriteEx(gdxHandle, write_to, "GAMS Transfer", 1)[0]:
                raise Exception(
                    f"Error opening GDX (w/compression) `{write_to}` for writing"
                )

        # setting special values
        specVals = gdx.doubleArray(gdx.GMS_SVIDX_MAX)
        specVals[gdx.GMS_SVIDX_UNDEF] = SpecialValues.UNDEF
        specVals[gdx.GMS_SVIDX_NA] = SpecialValues.NA
        specVals[gdx.GMS_SVIDX_EPS] = (
            SpecialValues.EPS if not eps_to_zero else gdx.GMS_SV_EPS
        )
        specVals[gdx.GMS_SVIDX_PINF] = SpecialValues.POSINF
        specVals[gdx.GMS_SVIDX_MINF] = SpecialValues.NEGINF

        rc = gdx.gdxSetSpecialValues(gdxHandle, specVals)
        assert rc

        #
        # register the universe
        # get UELS only once
        if uel_priority is None:
            uel_priority = []

        UELS = uel_priority + container.getUELs(symbols=symnames)

        # register UELs
        try:
            container._gams2np.gdxRegisterUels(gdxHandle, UELS)
        except Exception as err:
            raise err

        # capture container modified state
        orig_container_modified = container.modified

        # check if symbol domains are also being written -- if not, relax the domain for writing
        # retain the string set label, do not relax to "*" domains
        was_relaxed = {}
        for symobj in symobjs:
            if symobj.domain_type == "regular":
                if any(not isin(domsymobj, symobjs) for domsymobj in symobj.domain):
                    was_relaxed[symobj.name] = {
                        "object": symobj,
                        "domain": symobj.domain,
                        "modified": symobj.modified,
                    }

                    # relax the domain
                    symobj.domain = [
                        dom.name if isinstance(dom, abcs.AnyContainerSymbol) else dom
                        for dom in symobj.domain
                    ]

        #
        # main write
        for symname, symobj in zip(symnames, symobjs):
            if isinstance(symobj, abcs.AnyContainerAlias):
                if isinstance(symobj, abcs.ABCUniverseAlias):
                    gdx.gdxAddAlias(gdxHandle, "*", symname)
                else:
                    gdx.gdxAddAlias(gdxHandle, symobj.alias_with.name, symname)

            else:
                # adjust equation userinfo for GDX
                if isinstance(symobj, abcs.ABCEquation):
                    symobj._gams_subtype = (
                        symobj._gams_subtype + gdx.GMS_EQU_USERINFO_BASE
                    )

                if symobj.number_records == 0:
                    power_write_symbol_no_records(gdxHandle, symobj)

                elif symobj.number_records == 1 and symobj.dimension == 0:
                    power_write_symbol_scalar_record(gdxHandle, symobj)

                else:
                    # adjust write mode
                    if mode.casefold() == "category":
                        power_write_category(container, gdxHandle, symobj)

                    elif mode.casefold() == "string":
                        power_write_string(container, gdxHandle, symobj)

                    else:
                        raise Exception(f"Write mode not supported: {mode}")

            current_error_count = gdx.gdxDataErrorCount(gdxHandle)

            if current_error_count != 0:
                raise Exception(
                    f"Encountered data errors with symbol `{symname}`. "
                    "Possible causes are from duplicate records and/or domain violations. \n\n"
                    "Use 'hasDuplicateRecords', 'findDuplicateRecords', 'dropDuplicateRecords', "
                    "and/or 'countDuplicateRecords' to find/resolve duplicate records. \n"
                    "Use 'hasDomainViolations', 'findDomainViolations', 'dropDomainViolations', "
                    "and/or 'countDomainViolations' to find/resolve domain violations. \n\n"
                    "GDX file was not created successfully."
                )

    except Exception as err:
        # close file
        gdx.gdxClose(gdxHandle)
        gdx.gdxFree(gdxHandle)
        gdx.gdxLibraryUnload()

        # delete file
        if os.path.exists(write_to):
            os.remove(write_to)

        # raise error
        raise err

    finally:
        # restore domains in the Container
        for _, properties in was_relaxed.items():
            symobj = properties["object"]
            symobj._domain = properties["domain"]
            symobj._modified = properties["modified"]

        # reset container modified flag
        container._modified = orig_container_modified

    # auto convert file and close
    gdx.gdxAutoConvert(gdxHandle, 0)
    gdx.gdxClose(gdxHandle)
    gdx.gdxFree(gdxHandle)
    gdx.gdxLibraryUnload()


def power_write_symbol_no_records(
    gdxHandle, symobj: Union["Set", "Parameter", "Variable", "Equation"]
) -> None:
    """
    Write a GAMS symbol with no records to a GDX file.

    This function is used to write a GAMS symbol (Set, Parameter, Variable, or Equation) to a GDX file when the symbol
    has no records. It sets up the necessary information for the symbol, such as its name, description, dimension, type,
    and subtype. The symbol's domain is also defined based on its domain status (regular or relaxed).

    Parameters
    ----------
    gdxHandle: gdx.new_gdxHandle_tp()
        The GDX handle representing the GDX file where the symbol will be written.

    symobj: Set | Parameter | Variable | Equation
        The GAMS symbol (Set, Parameter, Variable, or Equation) to be written to the GDX file.
    """
    gdx.gdxDataWriteStrStart(
        gdxHandle,
        symobj.name,
        symobj.description,
        symobj.dimension,
        symobj._gams_type,
        symobj._gams_subtype,
    )

    # define domain
    if symobj._domain_status is DomainStatus.regular:
        gdx.gdxSymbolSetDomain(gdxHandle, symobj.domain_names)

    elif symobj._domain_status is DomainStatus.relaxed:
        ret, synr = gdx.gdxFindSymbol(gdxHandle, symobj.name)
        gdx.gdxSymbolSetDomainX(gdxHandle, synr, symobj.domain_names)

    else:
        ...

    gdx.gdxDataWriteDone(gdxHandle)


def power_write_symbol_scalar_record(
    gdxHandle, symobj: Union["Set", "Parameter", "Variable", "Equation"]
) -> None:
    """
    Write a GAMS symbol with a scalar record to a GDX file.

    This function is used to write a GAMS symbol (Set, Parameter, Variable, or Equation) to a GDX file when the symbol
    has a single scalar record. It sets up the necessary information for the symbol, such as its name, description,
    dimension, type, and subtype, and writes the scalar record to the GDX file.

    Parameters
    ----------
    gdxHandle: gdx.new_gdxHandle_tp()
        The GDX handle representing the GDX file where the symbol will be written.

    symobj: Set | Parameter | Variable | Equation
        The GAMS symbol (Set, Parameter, Variable, or Equation) with a scalar record to be written to the GDX file.
    """
    gdx.gdxDataWriteStrStart(
        gdxHandle,
        symobj.name,
        symobj.description,
        symobj.dimension,
        symobj._gams_type,
        symobj._gams_subtype,
    )

    vals = symobj.records.to_numpy().reshape((-1,))

    idx = np.arange(vals.size)
    arr = np.zeros(gdx.GMS_VAL_MAX, dtype=np.float64)
    arr[idx] = vals[idx]

    values = gdx.doubleArray(gdx.GMS_VAL_MAX)
    values[gdx.GMS_VAL_LEVEL] = arr[0]
    values[gdx.GMS_VAL_MARGINAL] = arr[1]
    values[gdx.GMS_VAL_LOWER] = arr[2]
    values[gdx.GMS_VAL_UPPER] = arr[3]
    values[gdx.GMS_VAL_SCALE] = arr[4]

    gdx.gdxDataWriteStr(gdxHandle, [], values)
    gdx.gdxDataWriteDone(gdxHandle)


def power_write_string(
    container: "Container",
    gdxHandle,
    symobj: Union["Set", "Parameter", "Variable", "Equation"],
) -> None:
    """
    Write a GAMS symbol to a GDX file with 'string' mode.

    Parameters
    ----------
    container: Container
        The Container containing the symbol to be written to the GDX file.

    gdxHandle: gdx.new_gdxHandle_tp()
        The GDX handle representing the GDX file where the symbol will be written.

    symobj: Set | Parameter | Variable | Equation
        The GAMS symbol (Set, Parameter, Variable, or Equation) to be written to the GDX file.
    """
    # get keys and values arrays
    arrkeys, arrvals = get_keys_and_values(symobj, mode="string")

    # final type checking
    if not isinstance(symobj, abcs.ABCSet):
        if not np.issubdtype(arrvals.dtype, np.floating):
            arrvals = arrvals.astype(float)

    # temporary adjustment to domain argument
    if symobj._domain_status is DomainStatus.regular:
        domain = symobj.domain_names
    elif symobj._domain_status is DomainStatus.relaxed:
        domain = ["*"] * symobj.dimension
    elif symobj._domain_status is DomainStatus.none:
        domain = None

    # power write
    try:
        container._gams2np.gdxWriteSymbolStr(
            gdxHandle,
            symobj.name,
            symobj.description,
            symobj.dimension,
            symobj._gams_type,
            symobj._gams_subtype,
            arrkeys,
            arrvals,
            domain,
        )
    except Exception as err:
        raise Exception(
            f"Error encountered when writing symbol `{symobj.name}`. "
            f"GDX Error: '{err}'. \n\n"
            "GDX file was not created successfully."
        )

    # assign actual relaxed domain labels
    if symobj._domain_status is DomainStatus.relaxed:
        ret, synr = gdx.gdxFindSymbol(gdxHandle, symobj.name)
        gdx.gdxSymbolSetDomainX(gdxHandle, synr, symobj.domain_names)


def power_write_category(
    container: "Container",
    gdxHandle,
    symobj: Union["Set", "Parameter", "Variable", "Equation"],
) -> None:
    """
    Write a GAMS symbol to a GDX file with 'categorical' mode.

    Parameters
    ----------
    container: Container
        The Container containing the symbol to be written to the GDX file.

    gdxHandle: gdx.new_gdxHandle_tp()
        The GDX handle representing the GDX file where the symbol will be written.

    symobj: Set | Parameter | Variable | Equation
        The GAMS symbol (Set, Parameter, Variable, or Equation) to be written to the GDX file.
    """
    # initialize major list
    majorList = [[]] * symobj.dimension

    for i in range(symobj.dimension):
        # create major list
        majorList[i] = symobj.getUELs(i)

    # get keys and values arrays
    arrkeys, arrvals = get_keys_and_values(symobj, mode="category")

    # final type checking
    if not np.issubdtype(arrkeys.dtype, np.integer):
        arrkeys = arrkeys.astype(int)

    if not isinstance(symobj, abcs.ABCSet):
        if not np.issubdtype(arrvals.dtype, np.floating):
            arrvals = arrvals.astype(float)

    # temporary adjustment to domain argument
    if symobj._domain_status is DomainStatus.regular:
        domain = symobj.domain_names
    elif symobj._domain_status is DomainStatus.relaxed:
        domain = ["*"] * symobj.dimension
    elif symobj._domain_status is DomainStatus.none:
        domain = None

    # power write
    try:
        container._gams2np.gdxWriteSymbolCat(
            gdxHandle,
            symobj.name,
            symobj.description,
            symobj.dimension,
            symobj._gams_type,
            symobj._gams_subtype,
            arrkeys,
            arrvals,
            majorList,
            domain,
        )

    except Exception as err:
        raise Exception(
            f"Error encountered when writing symbol `{symobj.name}`. "
            f"GDX Error: '{err}'. \n\n"
            "GDX file was not created successfully."
        )

    # assign actual relaxed domain labels
    if symobj._domain_status is DomainStatus.relaxed:
        ret, synr = gdx.gdxFindSymbol(gdxHandle, symobj.name)
        gdx.gdxSymbolSetDomainX(gdxHandle, synr, symobj.domain_names)
