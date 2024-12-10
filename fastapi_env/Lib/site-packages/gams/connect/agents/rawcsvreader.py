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

import math
import os
from gams.connect.agents.connectagent import ConnectAgent
from gams.core.gmd import *
import gams.transfer as gt
import pandas as pd


class RawCSVReader(ConnectAgent):

    def __init__(self, cdb, inst):
        super().__init__(cdb, inst)
        inst_raw = inst
        inst = self._normalize_instructions(inst)
        self._parse_options(inst)
        if self._trace > 0:
            self._log_instructions(inst, inst_raw)
        if self._trace > 3:
            pd.set_option("display.max_rows", None, "display.max_columns", None)

        self._check_symbol_exists(self._r_name)
        self._R = cdb._container.addSet(self._r_name, "*", description="Rows")

        self._check_symbol_exists(self._c_name)
        self._C = cdb._container.addSet(self._c_name, "*", description="Columns")

        self._check_symbol_exists(self._vs_name)
        self._VS = cdb._container.addSet(
            self._vs_name,
            [self._R, self._C],
            description="Cells with explanatory text",
        )

        self._check_symbol_exists(self._vu_name)
        self._VU = cdb._container.addSet(
            self._vu_name,
            [self._R, self._C, "*"],
            description="Cells with potential GAMS label",
        )

        self._check_symbol_exists(self._vf_name)
        self._VF = cdb._container.addParameter(
            self._vf_name,
            [self._R, self._C],
            description="Cells with numerical value",
        )
        self._read_csv_args = {
            "skipinitialspace": True,
            "keep_default_na": False,
            "na_values": "",
        }
        self._read_csv_args.update(self._read_csv_arguments)
        self._read_csv_args.update({"header": None})
        if self._read_as_string:
            self._read_csv_args.update({"dtype": str})

        self._trunc_org = {}
        self._trunc_issued = {}
        self._uel_list = []
        self._vu = []

    def _parse_options(self, inst):
        inst["file"] = os.path.abspath(inst["file"])
        self._csv_file = inst["file"]
        self._trace = inst["trace"]
        self._rowLabel = inst["rowLabel"]
        self._colLabel = inst["columnLabel"]
        self._read_as_string = inst["readAsString"]
        self._r_name = inst["rName"]
        self._c_name = inst["cName"]
        self._vs_name = inst["vsName"]
        self._vu_name = inst["vuName"]
        self._vf_name = inst["vfName"]
        self._read_csv_arguments = self._dict_get(inst, "readCSVArguments", {})

    def _utf8_lead_byte(self, b):
        # A UTF-8 intermediate byte starts with the bits 10xxxxxx.
        return (b & 0xC0) != 0x80

    def _utf8_byte_truncate(self, text, max_bytes):
        # If text[max_bytes] is not a lead byte, back up until a lead byte is
        # found and truncate before that character.
        utf8 = text.encode("utf8")
        if len(utf8) <= max_bytes:
            return text
        i = max_bytes
        while i > 0 and not self._utf8_lead_byte(utf8[i]):
            i -= 1
        return utf8[:i].decode("utf8")

    def _addUel(self, uel, keys):
        nuel = self._trunc_org.get(uel, -1)
        if nuel != -1:
            keys[2] = self._uel_list[nuel - 1]
            self._vu.append((*keys, uel))
            return True
        nuel = self._trunc_issued.get(uel, -1)
        if nuel == -1 and len(uel.encode("utf8")) < GLOBAL_UEL_IDENT_SIZE:
            if uel.find("'") != -1 and uel.find('"') != -1:
                return False
            if len(uel) and min(uel) < " ":
                return False
            self._uel_list.append(uel)
            nuel = len(self._uel_list)
            keys[2] = uel
            self._vu.append((*keys, uel))
            self._trunc_org[uel] = nuel
            self._trunc_issued[uel] = nuel
            return True
        # We need a new name for uel because it is too long or has already been issued as a trunc name
        next_trunc_nr = 0
        while True:
            next_trunc_nr += 1
            xs = "~" + str(next_trunc_nr)
            newname = (
                self._utf8_byte_truncate(uel, GLOBAL_UEL_IDENT_SIZE - len(xs) - 1) + xs
            )
            if (self._trunc_issued.get(newname, -1) == -1) and (
                self._trunc_org.get(newname, -1) == -1
            ):
                break

        if newname.find("'") != -1 and newname.find('"') != -1:
            return False
        if len(newname) and min(newname) < " ":
            return False
        self._uel_list.append(newname)
        nuel = len(self._uel_list)
        keys[2] = newname
        self._vu.append((*keys, self._utf8_byte_truncate(uel, GMS_SSSIZE - 2)))
        self._trunc_org[uel] = nuel
        self._trunc_issued[newname] = nuel
        return True

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")
        if self._trace > 1:
            self._cdb.print_log(
                f"Arguments for reading the CSV file:\n{self._read_csv_args}"
            )
        df = pd.read_csv(self._csv_file, **self._read_csv_args)
        if self._trace > 2:
            self._cdb.print_log(
                f"Raw DataFrame directly after reading the CSV file:\n{df}"
            )

        if self._trace > 1:
            self._cdb.print_log(f"DataFrame.shape: {df.shape}")
        self._R.setRecords([f"{self._rowLabel}{r+1}" for r in range(df.shape[0])])
        self._C.setRecords([f"{self._colLabel}{c+1}" for c in range(df.shape[1])])

        # Now go over cells
        vf = []
        vs = []
        skeys = [None] * 3
        for c in enumerate(df):
            skeys[1] = f"{self._colLabel}{c[0]+1}"
            for r in df[c[1]].items():
                cell_value = r[1]
                if isinstance(cell_value, float) and pd.isna(cell_value):
                    continue
                if isinstance(cell_value, str) and len(cell_value) == 0:
                    continue
                skeys[0] = f"{self._rowLabel}{r[0]+1}"
                if self._trace > 2:
                    self._cdb.print_log(
                        f"Cell {skeys[0]} {skeys[1]} {cell_value} type={type(cell_value)}"
                    )

                try:
                    dval = float(cell_value)
                    float_converted = not math.isfinite(dval)
                    if self._trace > 2:
                        self._cdb.print_log(f"  Float cell: {dval}")
                except:
                    dval = None
                    if isinstance(cell_value, str):
                        CELL_VALUE = cell_value.upper()
                    if CELL_VALUE == "EPS":
                        dval = gt.SpecialValues.EPS
                    elif CELL_VALUE == "NA":
                        dval = gt.SpecialValues.NA
                    elif CELL_VALUE == "UNDEF":
                        dval = gt.SpecialValues.UNDEF
                    elif CELL_VALUE == "TRUE":
                        dval = 1.0
                    elif CELL_VALUE == "FALSE":
                        dval = 0.0
                    if self._trace > 2 and isinstance(dval, float):
                        self._cdb.print_log(f"  Converted float: {dval}")
                    float_converted = True
                if isinstance(dval, float):
                    vf.append((*skeys[:-1], dval))
                if not isinstance(dval, float) or float_converted:
                    try:
                        sval = str(cell_value)
                        if self._trace > 2:
                            self._cdb.print_log(f"  Str cell: >{sval}<")
                        vs.append(
                            (
                                *skeys[:-1],
                                self._utf8_byte_truncate(sval, GMS_SSSIZE - 2),
                            )
                        )
                    except:
                        pass

                try:
                    sval = str(cell_value)
                    self._addUel(sval, skeys)
                except:
                    pass

        if len(vf):
            self._VF.setRecords(vf)
        if len(vs):
            self._VS.setRecords(vs)
        if len(self._vu):
            self._VU.setRecords(self._vu)

        # For symbols with None records, empty df is assigned
        self._transform_sym_none_to_empty(self._VF)
        self._transform_sym_none_to_empty(self._VS)
        self._transform_sym_none_to_empty(self._VU)

        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")
