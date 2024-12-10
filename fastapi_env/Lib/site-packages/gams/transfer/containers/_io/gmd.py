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

import copy
import pandas as pd
import numpy as np
from gams.core import gmd
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
    CasePreservingDict,
    SpecialValues,
    DomainStatus,
    convert_to_categoricals_cat,
    convert_to_categoricals_str,
    get_keys_and_values,
    generate_unique_labels,
    GAMS_VARIABLE_SUBTYPES,
    GAMS_EQUATION_SUBTYPES,
)


def container_read(container, load_from, symbols, records, mode, encoding):
    if len(container) == 0:
        initially_empty_container = True
    else:
        initially_empty_container = False

    save_spec_values = gmd.doubleArray(gmd.GMS_SVIDX_MAX)
    gmd.gmdGetUserSpecialValues(load_from, save_spec_values)

    # setting special values
    specVals = gmd.doubleArray(gmd.GMS_SVIDX_MAX)
    specVals[gmd.GMS_SVIDX_UNDEF] = SpecialValues.UNDEF
    specVals[gmd.GMS_SVIDX_NA] = SpecialValues.NA
    specVals[gmd.GMS_SVIDX_EPS] = SpecialValues.EPS
    specVals[gmd.GMS_SVIDX_PINF] = SpecialValues.POSINF
    specVals[gmd.GMS_SVIDX_MINF] = SpecialValues.NEGINF

    ret = gmd.gmdSetSpecialValues(load_from, specVals)
    assert ret

    # get number of symbols
    ret = gmd.gmdInfo(load_from, gmd.GMD_NRSYMBOLSWITHALIAS)
    symCount = ret[1]

    # find symbol metadata if not reading in all
    read_all_symbols = True
    SYMBOL_METADATA = []
    LINK_DOMAINS = []
    SYMBOLS_W_RECORDS = []

    rc = gmd.new_intp()

    if symbols is not None:
        read_all_symbols = False
        for sym in symbols:
            symptr = gmd.gmdFindSymbolWithAliasPy(load_from, sym, rc)
            if symptr is None:
                raise ValueError(
                    f"User specified to read symbol `{sym}`, "
                    "but it does not exist in the GMD object."
                )

            ret = gmd.gmdSymbolInfo(load_from, symptr, gmd.GMD_NUMBER)
            symnr = ret[1]
            SYMBOL_METADATA.append(
                gmd_get_metadata_by_number(container, load_from, symnr, encoding, rc)
            )

        # sort symbols by gmd number in order to read symbols in gmd order not user order
        SYMBOL_METADATA = sorted(SYMBOL_METADATA, key=lambda x: x["gmd_symbol_number"])

    # two paths to creating symbol objects
    if read_all_symbols:
        #
        #
        # fastpath if reading in all symbols (by number)
        for i in range(symCount):
            md = gmd_get_metadata_by_number(container, load_from, i, encoding, rc)

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

            # capture symbols to link later
            if (
                any(True if i is not None else False for i in md["domains_as_ptrs"])
                and md["type"] != gmd.GMS_DT_ALIAS
            ):
                LINK_DOMAINS.append(md)

            # capture symbols that have records (not aliases)
            if md["number_records"] > 0 and md["type"] != gmd.GMS_DT_ALIAS:
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

            # capture symbols to link later
            if (
                any(True if i is not None else False for i in md["domains_as_ptrs"])
                and md["type"] != gmd.GMS_DT_ALIAS
            ):
                LINK_DOMAINS.append(md)

            # capture symbols that have records (not aliases)
            if md["number_records"] > 0 and md["type"] != gmd.GMS_DT_ALIAS:
                SYMBOLS_W_RECORDS.append(md)

            # create the symbol object in the container
            create_symbol_from_metadata(container, md)

    #
    #
    # link domain objects
    READ_SYMBOLS = [md["name"] for md in SYMBOL_METADATA]
    for md in LINK_DOMAINS:
        domain = md["domain"]
        for n, d in enumerate(domain):
            if md["link_domains"][n] and d != "*" and d in READ_SYMBOLS:
                domain[n] = container[d]

        container[md["name"]]._domain

    # main records read
    if records:
        # get and store GMD_UELS
        GMD_UELS = container._gams2np.gmdGetUelList(load_from, encoding=encoding)
        GMD_UELS[0] = "*"

        for md in SYMBOLS_W_RECORDS:
            # get symbol object
            symobj = container[md["name"]]

            # fastpath for scalar symbols
            if md["dimension"] == 0 and md["number_records"] == 1:
                symptr = gmd.gmdGetSymbolByNumberPy(
                    load_from, md["gmd_symbol_number"] + 1, rc
                )
                recptr = gmd.gmdFindFirstRecordPy(load_from, symptr, rc)

                ret = gmd.gmdGetLevel(load_from, recptr)
                level = ret[1]

                marginal = 0.0
                lower = 0.0
                upper = 0.0
                scale = 0.0

                if md["type"] == gmd.GMS_DT_VAR or md["type"] == gmd.GMS_DT_EQU:
                    ret = gmd.gmdGetMarginal(load_from, recptr)
                    marginal = ret[1]
                    ret = gmd.gmdGetLower(load_from, recptr)
                    lower = ret[1]
                    ret = gmd.gmdGetUpper(load_from, recptr)
                    upper = ret[1]
                    ret = gmd.gmdGetScale(load_from, recptr)
                    scale = ret[1]

                vals = [level, marginal, lower, upper, scale]

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
                        ) = container._gams2np.gmdReadSymbolCat(
                            load_from,
                            md["name"],
                            GMD_UELS,
                            encoding=encoding,
                        )
                    except:
                        raise Exception(
                            f"Could not properly read symbol {md['name']} from GMD object. "
                            "Try setting read argument mode='string'"
                        )

                    # convert to categorical dataframe (return None if no data)
                    df = convert_to_categoricals_cat(arrkeys, arrvals, unique_uels)

                elif mode.casefold() == "string":
                    try:
                        arrkeys, arrvals = container._gams2np.gmdReadSymbolStr(
                            load_from,
                            md["name"],
                            encoding=encoding,
                        )
                    except:
                        raise Exception(
                            f"Could not properly read symbol {md['name']} from GMD object."
                        )

                    # convert to categorical dataframe (return None if no data)
                    df = convert_to_categoricals_str(arrkeys, arrvals, GMD_UELS[1:])

                else:
                    raise ValueError("Unrecognized read `mode`")

                # set records
                symobj._records = df

                # set column names
                symobj._records.columns = (
                    generate_unique_labels(symobj.domain_names) + symobj._attributes
                )

    gmd.delete_intp(rc)

    # reset GMD special values
    gmd.gmdSetSpecialValues(load_from, save_spec_values)


def gmd_get_metadata_by_number(container, load_from, symbol_number, encoding, rc):
    symptr = gmd.gmdGetSymbolByNumberPy(load_from, symbol_number + 1, rc)
    ret = gmd.gmdSymbolInfo(load_from, symptr, gmd.GMD_NAME)
    syid = ret[3]
    ret = gmd.gmdSymbolInfo(load_from, symptr, gmd.GMD_USERINFO)
    userinfo = ret[1]
    ret = gmd.gmdSymbolInfo(load_from, symptr, gmd.GMD_DIM)
    dimen = ret[1]
    ret = gmd.gmdSymbolInfo(load_from, symptr, gmd.GMD_NRRECORDS)
    nrecs = ret[1]
    expltxt = container._gams2np._gmdGetSymbolExplTxt(
        load_from, symptr, encoding=encoding
    )
    ret = gmd.gmdGetDomain(load_from, symptr, dimen)
    domains_as_ptrs = ret[1]
    domain = ret[2]
    ret = gmd.gmdSymbolType(load_from, symptr)
    typ = ret[1]

    if typ == gmd.GMS_DT_ALIAS:
        symptr = gmd.gmdFindSymbolPy(load_from, syid, rc)
        ret = gmd.gmdSymbolInfo(load_from, symptr, gmd.GMD_NAME)
        parent_set = ret[3]
    else:
        parent_set = None

    return {
        "name": syid,
        "gmd_symbol_number": symbol_number,
        "dimension": dimen,
        "type": typ,
        "userinfo": userinfo,
        "number_records": nrecs,
        "description": expltxt,
        "link_domains": [True if i is not None else False for i in domains_as_ptrs],
        "domains_as_ptrs": domains_as_ptrs,
        "domain": domain,
        "parent_set": parent_set,
    }


def create_symbol_from_metadata(container, metadata):
    # create the symbols in the container
    if metadata["type"] == gmd.GMS_DT_ALIAS:
        # test for universe alias
        if metadata["userinfo"] >= 0:
            try:
                Alias._from_gams(
                    container, metadata["name"], container[metadata["parent_set"]]
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
    elif metadata["type"] == gmd.GMS_DT_SET and metadata["userinfo"] == 0:
        Set._from_gams(
            container,
            metadata["name"],
            metadata["domain"],
            is_singleton=False,
            description=metadata["description"],
        )

    # singleton set
    elif metadata["type"] == gmd.GMS_DT_SET and metadata["userinfo"] == 1:
        Set._from_gams(
            container,
            metadata["name"],
            metadata["domain"],
            is_singleton=True,
            description=metadata["description"],
        )

    # parameters
    elif metadata["type"] == gmd.GMS_DT_PAR:
        Parameter._from_gams(
            container,
            metadata["name"],
            metadata["domain"],
            description=metadata["description"],
        )

    # variables
    elif metadata["type"] == gmd.GMS_DT_VAR:
        Variable._from_gams(
            container,
            metadata["name"],
            GAMS_VARIABLE_SUBTYPES.get(metadata["userinfo"], "free"),
            metadata["domain"],
            description=metadata["description"],
        )

    # equations
    elif metadata["type"] == gmd.GMS_DT_EQU:
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
            f"Unknown GamsDatabase (GMD) symbol classification (GAMS Type= {metadata['type']}, "
            f"GAMS Subtype= {metadata['userinfo']}). ",
            f"Cannot load symbol `{metadata['name']}`",
        )


def container_write(
    container, write_to, symbols, uel_priority, merge_symbols, mode, eps_to_zero
):
    if symbols is None:
        write_all_symbols = True
    else:
        write_all_symbols = False

    if write_all_symbols:
        symbols = container.listSymbols()

    # assert valid records
    container._assert_valid_records(symbols=symbols)

    # check if domain columns have valid categories
    symobjs = container.getSymbols(symbols)
    symnames = [sym.name for sym in symobjs]

    # GMD work
    save_spec_values = gmd.doubleArray(gmd.GMS_SVIDX_MAX)
    gmd.gmdGetUserSpecialValues(write_to, save_spec_values)

    # setting special values
    specVals = gmd.doubleArray(gmd.GMS_SVIDX_MAX)
    specVals[gmd.GMS_SVIDX_UNDEF] = SpecialValues.UNDEF
    specVals[gmd.GMS_SVIDX_NA] = SpecialValues.NA
    specVals[gmd.GMS_SVIDX_EPS] = (
        SpecialValues.EPS if not eps_to_zero else gmd.GMS_SV_EPS
    )
    specVals[gmd.GMS_SVIDX_PINF] = SpecialValues.POSINF
    specVals[gmd.GMS_SVIDX_MINF] = SpecialValues.NEGINF

    ret = gmd.gmdSetSpecialValues(write_to, specVals)
    assert ret

    # get number of symbols
    ret = gmd.gmdInfo(write_to, gmd.GMD_NRSYMBOLSWITHALIAS)
    symCount = ret[1]

    # read in all symbol metadata from GMD
    rc = gmd.new_intp()
    GMD_SYMBOL_METADATA = []
    for symnr in range(symCount):
        GMD_SYMBOL_METADATA.append(
            gmd_get_metadata_by_number(container, write_to, symnr, None, rc)
        )
    GMD_SYMBOLS = [md["name"] for md in GMD_SYMBOL_METADATA]

    # casefold key symbol lists
    CF_GMD_SYMBOLS = list(map(str.casefold, GMD_SYMBOLS))
    CF_CONTAINER_SYMBOLS = list(map(str.casefold, symnames))
    CF_MERGE_SYMBOLS = list(map(str.casefold, merge_symbols))

    # check if partial write is possible
    if not write_all_symbols:
        if any(i not in CF_GMD_SYMBOLS for i in CF_CONTAINER_SYMBOLS):
            raise Exception(
                "Writing a subset of symbols from a Container is only enabled for "
                "symbols that currently exist in the GamsDatabase (GMD) object."
                "This restriction may be relaxed in a future release."
            )

    # check symbols
    for symobj in symobjs:
        if not symobj.isValid():
            raise Exception(
                f"Cannot write to GMD because symbol `{symobj.name}` is invalid. "
                "Use `<symbol>.isValid(verbose=True)` to debug."
            )

    # check if merge is possible
    for i in merge_symbols:
        gmd_idx = CF_GMD_SYMBOLS.index(i.casefold())

        if i.casefold() not in CF_CONTAINER_SYMBOLS:
            raise Exception(
                f"User specified merge operation for symbol `{i}`, "
                f"however user did not specify that `{i}` should be written. "
                f"Add `{i}` to the 'symbols' argument."
            )

        if i.casefold() not in CF_GMD_SYMBOLS:
            raise Exception(
                f"User specified merge operation for symbol `{i}`, "
                "however symbol does not exist in the GMD object"
            )

        # check if symbol types are the same
        chk_type = GMD_SYMBOL_METADATA[gmd_idx]["type"]
        chk_userinfo = GMD_SYMBOL_METADATA[gmd_idx]["userinfo"]
        if (
            container[i]._gams_type != chk_type
            or container[i]._gams_subtype != chk_userinfo
        ):
            raise Exception(
                f"User specified merge operation for symbol `{i}`. "
                "However, symbols cannot be merged because container and GMD symbol types do not match"
            )

        if isinstance(container[i], abcs.ABCAlias):
            raise Exception(
                f"Alias symbols cannot be merged, remove symbol `{i}` "
                "from the merge_symbols list."
            )

        # check if the dimension is the same
        if container[i].dimension != GMD_SYMBOL_METADATA[gmd_idx]["dimension"]:
            raise Exception(
                f"User specified merge operation for symbol `{i}`. "
                "However, symbols cannot be merged because container and GMD symbol dimensions do not match"
            )

    # reorder symbols if necessary
    if container._isValidSymbolOrder() == False:
        container.reorderSymbols()

    #
    # register the universe
    # get UELS only once
    if uel_priority is None:
        uel_priority = []

    CONTAINER_UELS = uel_priority + container.getUELs(symbols=symbols)

    # register UELs
    for uel in CONTAINER_UELS:
        try:
            ret = gmd.gmdMergeUel(write_to, uel)
        except Exception as err:
            raise Exception(f"Unable to register UEL `{uel}` to GMD. Reason: {err}")

    # main write
    for symname, symobj in zip(CF_CONTAINER_SYMBOLS, symobjs):
        # True: merge, False: replace, None: new
        if symname in CF_MERGE_SYMBOLS:
            merge = True
        elif symname in CF_GMD_SYMBOLS and symname not in CF_MERGE_SYMBOLS:
            merge = False
        else:
            merge = None

        # write any aliases
        if isinstance(symobj, abcs.AnyContainerAlias):
            power_write_alias(write_to, symobj, rc)

        # all other symbols
        else:
            if symobj.number_records == 0:
                power_write_symbol_no_records(write_to, symobj, merge, rc)

            elif symobj.number_records == 1 and symobj.dimension == 0:
                power_write_symbol_scalar_record(
                    write_to, symobj, merge, eps_to_zero, rc
                )

            else:
                if mode.casefold() == "category":
                    power_write_category(
                        container, write_to, symobj, merge, eps_to_zero, rc
                    )

                elif mode.casefold() == "string":
                    power_write_string(
                        container, write_to, symobj, merge, eps_to_zero, rc
                    )

                else:
                    raise Exception(f"Write mode not supported: {mode}")

    gmd.delete_intp(rc)

    # reset GMD special values
    gmd.gmdSetSpecialValues(write_to, save_spec_values)


def power_write_alias(write_to, symobj, rc):
    if isinstance(symobj, abcs.ABCAlias):
        _, idx, _, _ = gmd.gmdSymbolInfo(
            write_to,
            gmd.gmdFindSymbolPy(write_to, symobj.alias_with.name, rc),
            gmd.GMD_NUMBER,
        )

        ret = gmd.gmdAddSymbolXPy(
            write_to,
            symobj.name,
            symobj.dimension,
            gmd.GMS_DT_ALIAS,
            idx,
            f"Aliased with {symobj.alias_with.name}",
            [None] * symobj.dimension,
            [""] * symobj.dimension,
            rc,
        )
    else:
        # universe aliases
        ret = gmd.gmdAddSymbolXPy(
            write_to,
            symobj.name,
            symobj.dimension,
            gmd.GMS_DT_ALIAS,
            -1,
            f"Aliased with {symobj.alias_with}",
            [None] * symobj.dimension,
            [""] * symobj.dimension,
            rc,
        )


def power_write_symbol_no_records(write_to, symobj, merge, rc):
    if merge is True:
        ...

    elif merge is False:
        symptr = gmd.gmdFindSymbolPy(write_to, symobj.name, rc)
        assert gmd.intp_value(
            rc
        ), f"internal error: could not find symbol {symobj.name} in gmd object"

        ret = gmd.gmdClearSymbol(write_to, symptr)
        assert (
            ret
        ), f"internal error: could not clear symbol {symobj.name} in gmd object"

    else:
        # get domain
        if symobj._domain_status is DomainStatus.regular:
            domain = []
            for d in symobj.domain_names:
                ret = gmd.gmdFindSymbolPy(write_to, d, rc)
                domain.append(ret)
        else:
            domain = [None] * symobj.dimension

        # create new symbol
        gmd.gmdAddSymbolXPy(
            write_to,
            symobj.name,
            symobj.dimension,
            symobj._gams_type,
            symobj._gams_subtype,
            symobj.description,
            domain,
            symobj.domain_names,
            rc,
        )


def power_write_symbol_scalar_record(write_to, symobj, merge, eps_to_zero, rc):
    def write_scalar_record(write_to, recptr, symobj):
        vals = symobj.records.to_numpy().reshape((-1,))

        if eps_to_zero:
            vals = [0.0 if val == 0 else val for val in vals]

        if symobj._gams_type == gmd.GMS_DT_PAR:
            ret = gmd.gmdSetLevel(write_to, recptr, vals[0])

        if symobj._gams_type == gmd.GMS_DT_VAR or symobj._gams_type == gmd.GMS_DT_EQU:
            ret = gmd.gmdSetLevel(write_to, recptr, vals[0])
            ret = gmd.gmdSetMarginal(write_to, recptr, vals[1])
            ret = gmd.gmdSetLower(write_to, recptr, vals[2])
            ret = gmd.gmdSetUpper(write_to, recptr, vals[3])
            ret = gmd.gmdSetScale(write_to, recptr, vals[4])

    if isinstance(merge, bool):
        symptr = gmd.gmdFindSymbolPy(write_to, symobj.name, rc)
        assert gmd.intp_value(rc), f"internal error: finding gmd symbol {symobj.name}"
        recptr = gmd.gmdMergeRecordPy(write_to, symptr, [], rc)
        assert gmd.intp_value(rc), "internal error: writing scalar record"
        write_scalar_record(write_to, recptr, symobj)

    else:
        symptr = gmd.gmdAddSymbolXPy(
            write_to,
            symobj.name,
            symobj.dimension,
            symobj._gams_type,
            symobj._gams_subtype,
            symobj.description,
            [],
            symobj.domain_names,
            rc,
        )
        recptr = gmd.gmdAddRecordPy(write_to, symptr, [], rc)
        write_scalar_record(write_to, recptr, symobj)


def power_write_string(container, write_to, symobj, merge, eps_to_zero, rc):
    # get keys and values arrays
    arrkeys, arrvals = get_keys_and_values(symobj, mode="string")

    if merge is True:
        symptr = gmd.gmdFindSymbolPy(write_to, symobj.name, rc)
        try:
            container._gams2np.gmdFillSymbolStr(
                write_to,
                symptr,
                arrkeys,
                arrvals,
                merge=True,
                relaxedType=False,
                epsToZero=eps_to_zero,
            )
        except Exception as err:
            # clear symbol records
            ret = gmd.gmdClearSymbol(write_to, symptr)
            raise Exception(
                f"Unable to successfully write symbol `{symobj.name}`.  Reason: {err}"
            )

    elif merge is False:
        symptr = gmd.gmdFindSymbolPy(write_to, symobj.name, rc)
        ret = gmd.gmdClearSymbol(write_to, symptr)

        try:
            container._gams2np.gmdFillSymbolStr(
                write_to,
                symptr,
                arrkeys,
                arrvals,
                merge=False,
                relaxedType=False,
                epsToZero=eps_to_zero,
            )
        except Exception as err:
            # clear symbol records
            ret = gmd.gmdClearSymbol(write_to, symptr)
            raise Exception(
                f"Unable to successfully write symbol `{symobj.name}`.  Reason: {err}"
            )
    else:
        # get domain
        if symobj._domain_status is DomainStatus.regular:
            domain = []
            for d in symobj.domain_names:
                ret = gmd.gmdFindSymbolPy(write_to, d, rc)
                domain.append(ret)
        else:
            domain = [None] * symobj.dimension

        # create new symbol
        symptr = gmd.gmdAddSymbolXPy(
            write_to,
            symobj.name,
            symobj.dimension,
            symobj._gams_type,
            symobj._gams_subtype,
            symobj.description,
            domain,
            symobj.domain_names,
            rc,
        )

        # fill new symbol
        try:
            container._gams2np.gmdFillSymbolStr(
                write_to,
                symptr,
                arrkeys,
                arrvals,
                merge=True,
                relaxedType=False,
                epsToZero=eps_to_zero,
            )

        except Exception as err:
            # clear symbol records
            ret = gmd.gmdClearSymbol(write_to, symptr)
            raise Exception(
                f"Unable to successfully write symbol `{symobj.name}`.  Reason: {err}"
            )


def power_write_category(container, write_to, symobj, merge, eps_to_zero, rc):
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

    if merge is True:
        symptr = gmd.gmdFindSymbolPy(write_to, symobj.name, rc)
        try:
            container._gams2np.gmdFillSymbolCat(
                write_to,
                symptr,
                arrkeys,
                arrvals,
                majorList,
                merge=True,
                relaxedType=False,
                epsToZero=eps_to_zero,
            )
        except Exception as err:
            # clear symbol records
            ret = gmd.gmdClearSymbol(write_to, symptr)
            raise Exception(
                f"Unable to successfully write symbol `{symobj.name}`.  Reason: {err}"
            )

    elif merge is False:
        symptr = gmd.gmdFindSymbolPy(write_to, symobj.name, rc)
        ret = gmd.gmdClearSymbol(write_to, symptr)

        try:
            container._gams2np.gmdFillSymbolCat(
                write_to,
                symptr,
                arrkeys,
                arrvals,
                majorList,
                merge=True,
                relaxedType=False,
                epsToZero=eps_to_zero,
            )
        except Exception as err:
            # clear symbol records
            ret = gmd.gmdClearSymbol(write_to, symptr)
            raise Exception(
                f"Unable to successfully write symbol `{symobj.name}`.  Reason: {err}"
            )
    else:
        # get domain
        if symobj._domain_status is DomainStatus.regular:
            domain = []
            for d in symobj.domain_names:
                ret = gmd.gmdFindSymbolPy(write_to, d, rc)
                domain.append(ret)
        else:
            domain = [None] * symobj.dimension

        # create new symbol
        symptr = gmd.gmdAddSymbolXPy(
            write_to,
            symobj.name,
            symobj.dimension,
            symobj._gams_type,
            symobj._gams_subtype,
            symobj.description,
            domain,
            symobj.domain_names,
            rc,
        )

        # fill new symbol
        try:
            container._gams2np.gmdFillSymbolCat(
                write_to,
                symptr,
                arrkeys,
                arrvals,
                majorList,
                merge=True,
                relaxedType=False,
                epsToZero=eps_to_zero,
            )

        except Exception as err:
            # clear symbol records
            ret = gmd.gmdClearSymbol(write_to, symptr)
            raise Exception(
                f"Unable to successfully write symbol `{symobj.name}`.  Reason: {err}"
            )
