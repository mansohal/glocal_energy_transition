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

from gams.core.gdx import *
from gams.core.gmd import *
import gams.control.workspace
import os

SV_UNDEF = GMS_SV_UNDEF
SV_EPS   = 4.94066E-324 #copied from value in C#

_spec_values = doubleArray(5)
_spec_values[0] = SV_UNDEF
_spec_values[1] = float('nan')
_spec_values[2] = float('inf')
_spec_values[3] = float('-inf')
_spec_values[4] = SV_EPS

_default_scale    = 1.0
_default_level    = 0.0
_default_marginal = 0.0
_par_level_default = 0.0

_var_lower_default = {}
_var_upper_default = {}

_equ_lower_default = {}
_equ_upper_default = {}

_var_lower_default[GMS_VARTYPE_UNKNOWN]  = 0.0
_var_lower_default[GMS_VARTYPE_BINARY]   = 0.0
_var_lower_default[GMS_VARTYPE_INTEGER]  = 0.0
_var_lower_default[GMS_VARTYPE_POSITIVE] = 0.0
_var_lower_default[GMS_VARTYPE_NEGATIVE] = _spec_values[GMS_SVIDX_MINF]
_var_lower_default[GMS_VARTYPE_FREE]     = _spec_values[GMS_SVIDX_MINF]
_var_lower_default[GMS_VARTYPE_SOS1]     = 0.0
_var_lower_default[GMS_VARTYPE_SOS2]     = 0.0
_var_lower_default[GMS_VARTYPE_SEMICONT] = 1.0
_var_lower_default[GMS_VARTYPE_SEMIINT]  = 1.0

_var_upper_default[GMS_VARTYPE_UNKNOWN]  = 0.0
_var_upper_default[GMS_VARTYPE_BINARY]   = 1.0
_var_upper_default[GMS_VARTYPE_INTEGER]  = 100.0
_var_upper_default[GMS_VARTYPE_POSITIVE] = _spec_values[GMS_SVIDX_PINF]
_var_upper_default[GMS_VARTYPE_NEGATIVE] = 0.0
_var_upper_default[GMS_VARTYPE_FREE]     = _spec_values[GMS_SVIDX_PINF]
_var_upper_default[GMS_VARTYPE_SOS1]     = _spec_values[GMS_SVIDX_PINF]
_var_upper_default[GMS_VARTYPE_SOS2]     = _spec_values[GMS_SVIDX_PINF]
_var_upper_default[GMS_VARTYPE_SEMICONT] = _spec_values[GMS_SVIDX_PINF]
_var_upper_default[GMS_VARTYPE_SEMIINT]  = 100.0

_equ_lower_default[GMS_EQUTYPE_E] = 0.0
_equ_lower_default[GMS_EQUTYPE_G] = 0.0
_equ_lower_default[GMS_EQUTYPE_L] = _spec_values[GMS_SVIDX_MINF]
_equ_lower_default[GMS_EQUTYPE_N] = _spec_values[GMS_SVIDX_MINF]
_equ_lower_default[GMS_EQUTYPE_X] = 0.0
_equ_lower_default[GMS_EQUTYPE_C] = 0.0

_equ_upper_default[GMS_EQUTYPE_E] = 0.0
_equ_upper_default[GMS_EQUTYPE_G] = _spec_values[GMS_SVIDX_PINF]
_equ_upper_default[GMS_EQUTYPE_L] = 0.0
_equ_upper_default[GMS_EQUTYPE_N] = _spec_values[GMS_SVIDX_PINF]
_equ_upper_default[GMS_EQUTYPE_X] = 0.0
_equ_upper_default[GMS_EQUTYPE_C] = _spec_values[GMS_SVIDX_PINF]

def _int_value_and_free(intP):
    intp_val = intp_value(intP)
    delete_intp(intP)
    return intp_val

class _GamsSymbolRecord(object):
    '''
    @brief This is the representation of a single record of a GamsSymbol.
    @details Derived classes are GamsEquationRecord, GamsParameterRecord, GamsSetRecord and GamsVariableRecord
    '''
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return bool(gmdSameRecord(self._symbol._database._gmd, self._sym_iter_ptr, other._sym_iter_ptr))
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)
        
    def get_keys(self):
        rc, keys = gmdGetKeys(self._symbol._database._gmd, self._sym_iter_ptr, self._symbol._dim)
        self._symbol._database._check_for_gmd_error(rc)
        return keys
    ## @brief Retrieve keys of GamsSymbolRecord
    keys = property(get_keys)

    def key(self, index):
        '''
        @brief Retrieve key of GamsSymbolRecord on position index
        @param index Index position of key to be returned
        @return Key at position index
        '''
        rc, key = gmdGetKey(self._symbol._database._gmd, self._sym_iter_ptr, index)
        self._symbol._database._check_for_gmd_error(rc)
        return key

    def get_symbol(self):
        return self._symbol
    ## @brief Retrieve the GamsSymbol that contains this record
    symbol = property(get_symbol)


    def __init__(self, symbol, sym_iter_ptr):
        #get already existing record from GMD
        symbol._database._workspace._debug_out("---- Entering _GamsSymbolRecord constructor ----", 0)
        self._symbol = symbol
        self._sym_iter_ptr = sym_iter_ptr

    def move_next(self):
        '''
        @brief Iterate to next GamsSymbolRecord of GamsSymbol
        @return True if everything worked, False otherwise
        '''
        rc = gmdRecordMoveNext(self._symbol._database._gmd, self._sym_iter_ptr)
        return bool(rc)

    def move_previous(self):
        '''
        @brief Iterate to previous GamsSymbolRecord of GamsSymbol
        @return True if everything worked, False otherwise
        '''
        rc = gmdRecordMovePrev(self._symbol._database._gmd, self._sym_iter_ptr)
        return bool(rc)

    def _keys_representation(self):
        s = self._symbol.name

        if self._symbol._dim>0:
            s += "("

        sep = False
        for k in self.keys:
            if sep: s+= ", "
            s += k
            sep = True

        if self._symbol._dim>0:
            s += ")"
        s += ":"
        return s

    def __del__(self):
        self._symbol._database._workspace._debug_out("---- Entering _GamsSymbolRecord destructor ----", 0)
        if self._sym_iter_ptr:
            rc = gmdFreeSymbolIterator(self._symbol._database._gmd, self._sym_iter_ptr)
            self._symbol._database._check_for_gmd_error(rc)
            self._sym_iter_ptr = None


class GamsEquationRecord(_GamsSymbolRecord):
    '''
    @brief This is the representation of a single record of a GamsEquation.
    '''

    def get_level(self):
        rc, v = gmdGetLevel(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_level(self, value):
        rc = gmdSetLevel(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the level of this record
    level = property(get_level, set_level)

    def get_marginal(self):
        rc, v = gmdGetMarginal(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_marginal(self, value):
        rc = gmdSetMarginal(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the marginal of this record
    marginal = property(get_marginal, set_marginal)

    def get_upper(self):
        rc, v = gmdGetUpper(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_upper(self, value):
        rc = gmdSetUpper(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the upper bound of this record
    upper = property(get_upper, set_upper)

    def get_lower(self):
        rc, v = gmdGetLower(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_lower(self, value):
        rc = gmdSetLower(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the lower bound of this record
    lower = property(get_lower, set_lower)

    def get_scale(self):
        rc, v = gmdGetScale(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_scale(self, value):
        rc = gmdSetScale(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the scale of this record
    scale = property(get_scale, set_scale)


    def __init__(self, equation, sym_iter_ptr):
        super(GamsEquationRecord, self).__init__(equation, sym_iter_ptr)

    ## @brief Retrieve a string representation of this record
    def __str__(self):
        s = self._keys_representation()

        level = self.level
        marginal = self.marginal
        lower = self.lower
        upper = self.upper
        scale = self.scale

        if level != _default_level:
            s += "  level=" + str(level)
        if marginal != _default_marginal:
            s += "  marginal=" + str(marginal)
        if lower != _equ_lower_default[self._symbol._equtype]:
            s += "  lower=" + str(lower)
        if upper != _equ_upper_default[self._symbol._equtype]:
            s += "  upper=" + str(upper)
        if scale != _default_scale:
            s += "  scale=" + str(scale)

        return s


class GamsParameterRecord(_GamsSymbolRecord):
    '''
    @brief This is the representation of a single record of a GamsParameter.
    '''
    def get_value(self):
        rc, v = gmdGetLevel(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_value(self, value):
        rc = gmdSetLevel(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the value of this record
    value = property(get_value, set_value)


    def __init__(self, set, sym_iter_ptr):
        super(GamsParameterRecord, self).__init__(set, sym_iter_ptr)

    ## @brief Retrieve a string representation of this record
    def __str__(self):
        s = self._keys_representation()

        value = self.value

        if value != _par_level_default:
            s += "  value=" + str(value)

        return s


class GamsSetRecord(_GamsSymbolRecord):
    '''
    @brief This is the representation of a single record of a GamsSet.
    '''
    def get_text(self):
        text = ""
        rc, text = gmdGetElemText(self._symbol._database._gmd, self._sym_iter_ptr)
        self._symbol._database._check_for_gmd_error(rc)
        return text
    def set_text(self, value):
        rc = gmdSetElemText(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the explanatory text of this record
    text = property(get_text, set_text)


    def __init__(self, set, sym_iter_ptr):
        super(GamsSetRecord, self).__init__(set, sym_iter_ptr)

    ## @brief Retrieve a string representation of this record
    def __str__(self):
        s = self._keys_representation()

        text = self.text
        if text != "" and text != " ":
            s += "  " + text
        else:
            s += "  yes"

        return s


class GamsVariableRecord(_GamsSymbolRecord):
    '''
    @brief This is the representation of a single record of a GamsVariable.
    '''

    #TODO: additional get_variable call beside get_symbol call in GamsSymbolRecord?

    def get_level(self):
        rc, v = gmdGetLevel(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_level(self, value):
        rc = gmdSetLevel(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the level of this record
    level = property(get_level, set_level)

    def get_marginal(self):
        rc, v = gmdGetMarginal(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_marginal(self, value):
        rc = gmdSetMarginal(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the marginal of this record
    marginal = property(get_marginal, set_marginal)

    def get_upper(self):
        rc, v = gmdGetUpper(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_upper(self, value):
        rc = gmdSetUpper(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the upper bound of this record
    upper = property(get_upper, set_upper)

    def get_lower(self):
        rc, v = gmdGetLower(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_lower(self, value):
        rc = gmdSetLower(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the lower bound of this record
    lower = property(get_lower, set_lower)

    def get_scale(self):
        rc, v = gmdGetScale(self._symbol._database._gmd, self._sym_iter_ptr)
        if rc:
            return v
        else:
            return float('nan')
    def set_scale(self, value):
        rc = gmdSetScale(self._symbol._database._gmd, self._sym_iter_ptr, value)
        self._symbol._database._check_for_gmd_error(rc)
    ## @brief Get or set the scale of this record
    scale = property(get_scale, set_scale)


    def __init__(self, variable, sym_iter_ptr):
        super(GamsVariableRecord, self).__init__(variable, sym_iter_ptr)

    ## @brief Retrieve a string representation of this record
    def __str__(self):
        s = self._keys_representation()

        level = self.level
        marginal = self.marginal
        lower = self.lower
        upper = self.upper
        scale = self.scale

        if level != _default_level:
            s += "  level=" + str(level)
        if marginal != _default_marginal:
            s += "  marginal=" + str(marginal)
        if lower != _var_lower_default[self._symbol._vartype]:
            s += "  lower=" + str(lower)
        if upper != _var_upper_default[self._symbol._vartype]:
            s += "  upper=" + str(upper)
        if scale != _default_scale:
            s += "  scale=" + str(scale)

        return s

class _GamsSymbol(object):
    '''
    @brief This is the representation of a symbol in GAMS.
    @details It exists in a GamsDatabase and contains GamsSymbolRecords which one can iterate through.
             Derived classes are GamsEquation, GamsParameter, GamsSet and GamsVariable.
    '''
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._sym_ptr == other._sym_ptr
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_domains(self):
        if self._domains == None:
            self._domains = []
            if self._dim == 0:
                return self._domains
            retDom = gmdGetDomain(self._database._gmd, self._sym_ptr, self._dim)
            self._database._check_for_gmd_error(retDom[0])
            domains = retDom[1]
            for i in range(self._dim):
                if domains[i] != None:
                    retSym = gmdSymbolInfo(self._database._gmd, domains[i], GMD_NAME)
                    self._database._check_for_gmd_error(retSym[0])
                    name = retSym[3]
                    if name == '*':
                        self._domains.append('*')
                    else:
                        self._domains.append(GamsSet(self._database, sym_ptr = domains[i]))
                else:
                    self._domains.append(retDom[2][i])
        return self._domains

    ## @brief Domains of Symbol, each element is either a GamsSet (real domain) or a string (relaxed domain)
    domains = property(get_domains)
    
    def get_domains_as_strings(self):
        if self._domains_as_strings == None:
            self._domains_as_strings = []
            if self._dim == 0:
                return self._domains_as_strings
            ret = gmdGetDomain(self._database._gmd, self._sym_ptr, self._dim)
            self._database._check_for_gmd_error(ret[0])
            
            for i in range(self._dim):
                self._domains_as_strings.append(ret[2][i]);
        return self._domains_as_strings
    
    ## @brief Domains of Symbol, each element is a string. Note: If the domains is as alias in GAMS, this call will return the name of the alias, not the name of the aliased set
    domains_as_strings = property(get_domains_as_strings)

    def get_dimension(self):
        return self._dim
    ## @brief Get GamsSymbol dimension
    dimension = property(get_dimension)

    def get_text(self):
        return self._text
    ## @brief Get explanatory text of GamsSymbol
    text = property(get_text)

    def get_name(self):
        return self._name
    ## Get GamsSymbol name
    name = property(get_name)

    def get_database(self):
        return self._database
    ## @brief Get GamsDatabase containing GamsSymbol
    database = property(get_database)

    def get_number_records(self):
        ret = gmdSymbolInfo(self._database._gmd, self._sym_ptr, GMD_NRRECORDS)
        self._database._check_for_gmd_error(ret[0])
        return ret[1]
    ## @brief Retrieve the number of records of the GamsSymbol
    #  @note This is the same as calling len(symbol)
    number_records = property(get_number_records)

    ## @brief Retrieve the number of records of the GamsSymbol
    def __len__(self):
        return self.get_number_records()

    def __init__(self, database, identifier=None, dimension=None, explanatory_text="", sym_ptr=None):
        database._workspace._debug_out("---- Entering _GamsSymbol constructor ----", 0)
        self._sym_iter_ptr = None
        self._database = database
        self._domains = None
        self._domains_as_strings = None

        #receive an already existing symbol from GMD
        if not (identifier or dimension or explanatory_text) and sym_ptr:
            if sym_ptr == None:
                raise gams.control.workspace.GamsException("Symbol does not exist");

            self._sym_ptr = sym_ptr;

            rc, type = gmdSymbolType(self._database._gmd, self._sym_ptr)
            self._database._check_for_gmd_error(rc)

            rc, ival, dval, self._name = gmdSymbolInfo(self._database._gmd, self._sym_ptr, GMD_NAME)
            self._database._check_for_gmd_error(rc)

            rc, self._dim, dval, sval = gmdSymbolInfo(self._database._gmd, self._sym_ptr, GMD_DIM)
            self._database._check_for_gmd_error(rc)

            rc, ival, dval, self._text = gmdSymbolInfo(self._database._gmd, self._sym_ptr, GMD_EXPLTEXT)
            self._database._check_for_gmd_error(rc)

        #create a new symbol in GMD
        elif not sym_ptr and identifier and dimension != None:
            if dimension < 0 or dimension > GMS_MAX_INDEX_DIM:
                raise gams.control.workspace.GamsException("Invalid dimension specified " + str(dimension) + " is not in [0," + str(GMS_MAX_INDEX_DIM) + "]")
            self._name = identifier
            self._dim = dimension
            self._text = explanatory_text

        else:
            raise gams.control.workspace.GamsException("Invalid combination of parameters")

    def __del__(self):
        self._database._workspace._debug_out("---- Entering _GamsSymbol destructor ----", 0)
        if self._sym_iter_ptr:
            rc = gmdFreeSymbolIterator(self._database._gmd, self._sym_iter_ptr)
            self._database._check_for_gmd_error(rc)
            self._sym_iter_ptr = None

    def copy_symbol(self, target):
        '''
        @brief Copys all records from the GamsSymbol to the target GamsSymbol (if target had records, they will be deleted)
        @param target Target GamsSymbol
        @returns True if everything worked, else false
        '''
        if target._database._record_lock:
            raise gams.control.workspace.GamsException("Cannot add data records to record-locked database")
        rc = gmdCopySymbol(self._database._gmd, target._sym_ptr, self._sym_ptr)
        self._database._check_for_gmd_error(rc)
        return True

    def _check_keys(self, keys):
        if len(keys) != self._dim:
            raise gams.control.workspace.GamsException("Different dimensions: " + str(len(keys)) + " vs. " + str(self._dim))
        for i in range(self._dim):
            if keys[i] == None:
                raise gams.control.workspace.GamsException("'Key' not allowed to be None (found at dimension " + str(i+1) + ")")

    def delete_record(self, keys=None):
        '''
        @brief Delete GamsSymbol record
        @param keys List of keys
        @return True if everything worked, else False
        '''
        if self._database._record_lock:
            raise gams.control.workspace.GamsException("Cannot remove data records to record-locked database")
        if not (isinstance(keys, str) or isinstance(keys,list) or isinstance(keys, tuple) or keys==None):
            raise gams.control.workspace.GamsException("Wrong type of keys argument in delete_record. Valid types are 'str', 'list', 'tuple' and their subclasses")
        if isinstance(keys, str):
            keys = [keys]
        elif isinstance(keys, tuple):
            keys = list(keys)
        elif not keys:
            keys = []
        self._check_keys(keys)
        rc = new_intp()
        sym_iter_ptr = gmdFindRecordPy(self._database._gmd, self._sym_ptr, keys, rc)
        if not _int_value_and_free(rc):
            return False
        rc = gmdDeleteRecord(self._database._gmd, sym_iter_ptr)
        self._database._check_for_gmd_error(rc)
        rc = gmdFreeSymbolIterator(self._database._gmd, sym_iter_ptr)
        self._database._check_for_gmd_error(rc)
        sym_iter_ptr = None
        return True

    def clear(self):
        '''
        @brief Clear symbol
        @returns True if everything worked, else False
        '''
        if self._database._record_lock:
            raise gams.control.workspace.GamsException("Cannot remove data records to record-locked database")
        return bool(gmdClearSymbol(self._database._gmd, self._sym_ptr))

    def __iter__(self):
        self._sym_iter_ptr = None
        return self

    def _concat_keys(self, keys):
        if not keys or len(keys) == 0:
            return ""
        else:
            ret = ""
            for i in range(len(keys)-1):
                ret += keys[i] + ","
            ret += keys[len(keys)-1]
            return ret

    def _check_and_return_record(self, sym_iter_ptr, cb_msg):
        if sym_iter_ptr == None:
            raise gams.control.workspace.GamsException(cb_msg())
        if self._sym_ptr == None:
            raise gams.control.workspace.GamsException("Invalid Pointer")
        if isinstance(self, GamsVariable):
            return GamsVariableRecord(self, sym_iter_ptr)
        if isinstance(self, GamsEquation):
            return GamsEquationRecord(self, sym_iter_ptr)
        if isinstance(self, GamsParameter):
            return GamsParameterRecord(self, sym_iter_ptr)
        if isinstance(self, GamsSet):
            return GamsSetRecord(self, sym_iter_ptr)
        else:
            raise gams.control.workspace.GamsException("Invalid symbol type")

    def next(self):
        
        if self._sym_iter_ptr == None:
            rc = new_intp()
            self._sym_iter_ptr = gmdFindFirstRecordPy(self._database._gmd, self._sym_ptr, rc)
            delete_intp(rc)
            if self._sym_iter_ptr == None:
                raise StopIteration
        else:
            if not gmdRecordMoveNext(self._database._gmd, self._sym_iter_ptr):
                raise StopIteration
        if self._sym_iter_ptr == None:
            raise StopIteration
        else:
            cb_msg = lambda: "No next record available in symbol '" + self._name + "'"
            rc = new_intp()
            rec = gmdCopySymbolIteratorPy(self._database._gmd, self._sym_iter_ptr, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))
            return self._check_and_return_record(rec, cb_msg)
            
    def __next__(self):
        return self.next()

    def find_record(self, keys=None):
        '''
        @brief Find record in GamsSymbol
        @param keys List of keys
        @return Reference to found record
        '''
        if not (isinstance(keys, str) or isinstance(keys,list) or isinstance(keys, tuple) or keys==None):
            raise gams.control.workspace.GamsException("Wrong type of keys argument in find_record. Valid types are 'str', 'list', 'tuple' and their subclasses")
        if not keys:
            keys = []
        if isinstance(keys, str):
            keys = [keys]
        elif isinstance(keys, tuple):
            keys = list(keys)
        self._check_keys(keys)
        rc = new_intp()
        sym_iter_ptr = gmdFindRecordPy(self._database._gmd, self._sym_ptr, keys, rc)
        self._database._check_for_gmd_error(_int_value_and_free(rc))
        cb_msg = lambda: "Cannot find record '" + self._concat_keys(keys) + "' in symbol '" + self._name + "'"
        return self._check_and_return_record(sym_iter_ptr, cb_msg)

    def __getitem__(self, keys=None):
        return self.find_record(keys)

    def add_record(self, keys=None):
        '''
        @brief Add record to GamsSymbol
        @param keys List of keys
        @return Reference to added record
        '''
        if self._database._record_lock:
            raise gams.control.workspace.GamsException("Cannot add data records to record-locked database")
        if not (isinstance(keys, str) or isinstance(keys,list) or isinstance(keys, tuple) or keys==None):
            raise gams.control.workspace.GamsException("Wrong type of keys argument in add_record. Valid types are 'str', 'list', 'tuple' and their subclasses")
        if isinstance(keys, str):
            keys = [keys]
        elif isinstance(keys, tuple):
            keys = list(keys)
        elif not keys:
            keys = []
        self._check_keys(keys)
        rc = new_intp()
        sym_iter_ptr = gmdAddRecordPy(self._database._gmd, self._sym_ptr, keys, rc)
        self._database._check_for_gmd_error(_int_value_and_free(rc))
        cb_msg = lambda: "Record '" + self._concat_keys(keys) + "' aleady exists in symbol '" + self._name + "'"
        return self._check_and_return_record(sym_iter_ptr, cb_msg)

    def merge_record(self, keys=None):
        '''
        @brief Finds record in GamsSymbol if it exists, adds it if not
        @param keys List of keys
        @return Reference to found or added record
        '''
        if not (isinstance(keys, str) or isinstance(keys,list) or isinstance(keys, tuple) or keys==None):
            raise gams.control.workspace.GamsException("Wrong type of keys argument in merge_record. Valid types are 'str', 'list', 'tuple' and their subclasses")
        if not keys:
            keys = []
        if isinstance(keys, str):
            keys = [keys]
        elif isinstance(keys, tuple):
            keys = list(keys)
        self._check_keys(keys)
        rc = new_intp()
        sym_iter_ptr = gmdFindRecordPy(self._database._gmd, self._sym_ptr, keys, rc)
        delete_intp(rc)
        #self._database._check_for_gmd_error(intp_value(rc))
        if sym_iter_ptr != None:
            cb_msg = lambda: "Cannot find record '" + self._concat_keys(keys) + "' in symbol '" + self._name + "'"
            return self._check_and_return_record(sym_iter_ptr, cb_msg)
        else:
            if self._database._record_lock:
                raise gams.control.workspace.GamsException("Cannot add data records to record-locked database")
            rc = new_intp()
            sym_iter_ptr = gmdAddRecordPy(self._database._gmd, self._sym_ptr, keys, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))
            cb_msg = lambda: "Record '" + self._concat_keys(keys) + "' could neither be found in nor added to symbol '" + self._name + "'"
            return self._check_and_return_record(sym_iter_ptr, cb_msg)

    def first_record(self, slice=None):
        '''
        @brief Retrieve first record in GamsSymbol
        @param slice Define filter for elements whose record should be retrieved
        @code{.py}
        print("Transportation costs from Seattle")
        record = job.out_db.get_parameter("c").first_record(["seattle", " "])
        @endcode
        @return Reference to record
        '''
        if not slice:
            rc = new_intp()
            sym_iter_ptr = gmdFindFirstRecordPy(self._database._gmd, self._sym_ptr, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))
            cb_msg = lambda: "Symbol '" + self._name + "' is empty"
        else:
            if not (isinstance(slice, str) or isinstance(slice,list) or isinstance(slice, tuple) or keys==None):
                raise gams.control.workspace.GamsException("Wrong type of slice argument in first_record. Valid types are 'str', 'list', 'tuple' and their subclasses")
            if isinstance(slice, str):
                slice = [slice]
            elif isinstance(slice, tuple):
                slice = list(slice)
            if len(slice) != self._dim:
                raise gams.control.workspace.GamsException("Different dimensions: " + str(len(slice)) + " vs. " + str(self._dim))
            rc = new_intp()
            sym_iter_ptr = gmdFindFirstRecordSlicePy(self._database._gmd, self._sym_ptr, slice, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))
            cb_msg = lambda: "No record with slice '" + self._concat_keys(slice) + "' found in symbol '" + self._name + "'"
        return self._check_and_return_record(sym_iter_ptr, cb_msg)

    def last_record(self, slice=None):
        if not slice:
            rc = new_intp()
            sym_iter_ptr = gmdFindLastRecordPy(self._database._gmd, self._sym_ptr, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))
            cb_msg = lambda: "Symbol '" + self._name + "' is empty"
        else:
            if not (isinstance(slice, str) or isinstance(slice,list) or isinstance(slice, tuple) or keys==None):
                raise gams.control.workspace.GamsException("Wrong type of slice argument in last_record. Valid types are 'str', 'list', 'tuple' and their subclasses")
            if isinstance(slice, str):
                slice = [slice]
            elif isinstance(slice, tuple):
                slice = list(slice)
            if len(slice) != self._dim:
                raise gams.control.workspace.GamsException("Different dimensions: " + str(len(slice)) + " vs. " + str(self._dim))
            rc = new_intp()
            sym_iter_ptr = gmdFindLastRecordSlicePy(self._database._gmd, self._sym_ptr, slice, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))
            cb_msg = lambda: "No record with slice '" + self._concat_keys(slice) + "' found in symbol '" + self._name + "'"
        return self._check_and_return_record(sym_iter_ptr, cb_msg)

    def check_domains(self):
        '''
        @brief Check if all records are within the specified domain of the symbol
        @return True: Everything is correct, False: There is a domain violation
        '''
        has_violation = new_intp()
        rc = gmdCheckSymbolDV(self._database._gmd, self._sym_ptr, has_violation)
        self._database._check_for_gmd_error(rc)
        if _int_value_and_free(has_violation) == 1:
            return False
        else:
            return True


    def get_symbol_dvs(self, max_viol = 0):
        '''
        @brief return all GamsSymbolDomainViolations
        @param max_viol The maximum number of domain violations which should be stored (0 for no limit)
        @return List containing GamsSymbolDomainViolation objects
        '''

        ret_list = []
        rc = new_intp()
        dv_handle = gmdGetFirstDVInSymbolPy(self._database._gmd, self._sym_ptr, rc)
        self._database._check_for_gmd_error(_int_value_and_free(rc))
        has_next = False
        if dv_handle != None:
            has_next = True

        while has_next and (len(ret_list) < max_viol or max_viol == 0):
            rc = new_intp()
            rec = gmdGetDVSymbolRecordPy (self._database._gmd, dv_handle, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))

            violation_idx = intArray(self._dim)
            rc = gmdGetDVIndicator (self._database._gmd, dv_handle, violation_idx)
            self._database._check_for_gmd_error(rc)

            violation_idx_list = []
            for i in range(self._dim):
                violation_idx_list.append(bool(violation_idx[i]))

            rc, type = gmdSymbolType(self._database._gmd, self._sym_ptr)
            self._database._check_for_gmd_error(rc)
            symbol_record = None

            if type == dt_equ:
                symbol_record = GamsEquationRecord(self, rec)
            elif type == dt_var:
                symbol_record = GamsVariableRecord(self, rec)
            elif type == dt_par:
                symbol_record = GamsParameterRecord(self, rec)
            elif type == dt_set:
                symbol_record = GamsSetRecord(self, rec)

            ret_list.append( GamsSymbolDomainViolation(violation_idx_list, symbol_record) )

            has_next = new_intp()
            rc = gmdMoveNextDVInSymbol(self._database._gmd, dv_handle, has_next)
            self._database._check_for_gmd_error(rc)
            has_next = bool(_int_value_and_free(has_next))

        rc = gmdDomainCheckDone(self._database._gmd)
        self._database._check_for_gmd_error(rc)
        rc = gmdFreeDVHandle(self._database._gmd, dv_handle)
        self._database._check_for_gmd_error(rc)
        return ret_list

class GamsVariable(_GamsSymbol):
    '''
    @brief This is the representation of a variable symbol in GAMS.
    @details It exists in a GamsDatabase and contains GamsVariableRecords which one can iterate through.
    '''
    def get_vartype(self):
        return self._vartype
    ## @brief Retrieve subtype of variable (VarType.Binary, VarType.Integer, VarType.Positive, VarType.Negative, VarType.Free, VarType.SOS1, VarType.SOS2, VarType.SemiCont, VarType.SemiInt)
    vartype = property(get_vartype)

    def __init__(self, database, identifier=None, dimension=None, vartype=None, explanatory_text="", sym_ptr=None, domains=None):
        if identifier and (vartype != None) and (domains != None) and not dimension:
            super(GamsVariable, self).__init__(database, identifier, len(domains), explanatory_text, sym_ptr)
        else:
            super(GamsVariable, self).__init__(database, identifier, dimension, explanatory_text, sym_ptr)

        #receive an already existing symbol from GMD
        if not (identifier or dimension or vartype or explanatory_text) and sym_ptr:
            rc, subtype, dval, sval = gmdSymbolInfo(self._database._gmd, self._sym_ptr, GMD_USERINFO)
            self._database._check_for_gmd_error(rc)
            self._vartype = subtype

        #create new variable in GMD
        elif not sym_ptr and identifier and dimension != None and vartype != None:
            self._vartype = vartype
            rc = new_intp()
            self._sym_ptr = gmdAddSymbolPy(self._database._gmd, self._name, self._dim, dt_var, self._vartype, self._text, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))

        #create new variable with domain information
        elif identifier and (vartype != None) and (domains != None) and not dimension:
            if not isinstance(domains, (list, tuple)):
                raise gams.control.workspace.GamsException("Parameter domains has to be a list or a tuple")

            self._vartype = vartype
            if len(domains) == 0:
                rc = new_intp()
                self._sym_ptr = gmdAddSymbolPy(self._database._gmd, self._name, self._dim, dt_var, self._vartype, self._text, rc)
                self._database._check_for_gmd_error(_int_value_and_free(rc))
            else:
                dom_ptr = [None]*self._dim
                rel_dom = [""]*self._dim

                for i in range(self._dim):
                    if isinstance(domains[i], GamsSet):
                        dom_ptr[i] = domains[i]._sym_ptr
                    elif isinstance(domains[i], str):
                        rel_dom[i] = domains[i]
                    else:
                        raise gams.control.workspace.GamsException("Domain must be GamsSet or string but saw " + str(type(domains[i])) + " on index " + str(i))
                rc = new_intp()
                self._sym_ptr = gmdAddSymbolXPy(self._database._gmd, self._name, self._dim, dt_var, self._vartype, self._text, dom_ptr, rel_dom, rc)
                self._database._check_for_gmd_error(_int_value_and_free(rc))
        else:
            raise gams.control.workspace.GamsException("Invalid combination of parameters")


class GamsParameter(_GamsSymbol):
    '''
    @brief This is the representation of a parameter symbol in GAMS.
    @details It exists in a GamsDatabase and contains GamsParameterRecords which one can iterate through.
    '''

    def __init__(self, database, identifier=None, dimension=None, explanatory_text="", sym_ptr=None, domains=None):
        if identifier and (domains != None) and not dimension:
            super(GamsParameter, self).__init__(database, identifier, len(domains), explanatory_text, sym_ptr)
        else:
            super(GamsParameter, self).__init__(database, identifier, dimension, explanatory_text, sym_ptr)

        #receive an already existing symbol from GMD - nothing to do
        if not (identifier or dimension or explanatory_text) and sym_ptr:
            pass

        #create new parameter in GMD
        elif not sym_ptr and identifier and dimension != None:
            rc = new_intp()
            self._sym_ptr = gmdAddSymbolPy(self._database._gmd, self._name, self._dim, dt_par, 0, self._text, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))
            if self._sym_ptr == None:
                raise gams.control.workspace.GamsException("Cannot create parameter " + self._name)

        #create new parameter with domain information
        elif identifier and (domains != None) and not dimension:
            if not isinstance(domains, (list, tuple)):
                raise gams.control.workspace.GamsException("Parameter domains has to be a list or a tuple")

            if len(domains) == 0:
                rc = new_intp()
                self._sym_ptr = gmdAddSymbolPy(self._database._gmd, self._name, self._dim, dt_par, 0, self._text, rc);
                self._database._check_for_gmd_error(_int_value_and_free(rc))
            else:
                dom_ptr = [None]*self._dim
                rel_dom = [""]*self._dim

                for i in range(self._dim):
                    if isinstance(domains[i], GamsSet):
                        dom_ptr[i] = domains[i]._sym_ptr
                    elif isinstance(domains[i], str):
                        rel_dom[i] = domains[i]
                    else:
                        raise gams.control.workspace.GamsException("Domain must be GamsSet or string but saw " + str(type(domains[i])) + " on index " + str(i))
                rc = new_intp()
                self._sym_ptr = gmdAddSymbolXPy(self._database._gmd, self._name, self._dim, dt_par, 0, self._text, dom_ptr, rel_dom, rc)
                self._database._check_for_gmd_error(_int_value_and_free(rc))

        else:
            raise gams.control.workspace.GamsException("Invalid combination of parameters")


class GamsSet(_GamsSymbol):
    '''
    @brief This is the representation of a set symbol in GAMS.
    @details It exists in a GamsDatabase and contains GamsSetRecords which one can iterate through.
    '''
    def get_settype(self):
        return self._settype
    ## @brief Retrieve subtype of set (SetType.Multi, SetType.Singleton)
    settype = property(get_settype)

    def __init__(self, database, identifier=None, dimension=None, explanatory_text="", sym_ptr=None, domains=None, settype=0):
        if identifier and (domains != None) and not dimension:
            super(GamsSet, self).__init__(database, identifier, len(domains), explanatory_text, sym_ptr)
        else:
            super(GamsSet, self).__init__(database, identifier, dimension, explanatory_text, sym_ptr)

        #receive an already existing symbol from GMD
        if not (identifier or dimension or explanatory_text) and sym_ptr:
            rc, subtype, dval, sval = gmdSymbolInfo(self._database._gmd, self._sym_ptr, GMD_USERINFO)
            self._database._check_for_gmd_error(rc)
            self._settype = subtype

        #create new set in GMD
        elif not sym_ptr and identifier and dimension != None:
            self._settype = settype
            rc = new_intp()
            self._sym_ptr = gmdAddSymbolPy(self._database._gmd, self._name, self._dim, dt_set, self._settype, self._text, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))

        #create new set with domain information
        elif identifier and (domains != None) and not dimension:
            if not isinstance(domains, (list, tuple)):
                raise gams.control.workspace.GamsException("Parameter domains has to be a list or a tuple")

            self._settype = settype
            if len(domains) == 0:
                rc = new_intp()
                self._sym_ptr = gmdAddSymbolPy(self._database._gmd, self._name, self._dim, dt_set, self._settype, self._text, rc)
                self._database._check_for_gmd_error(_int_value_and_free(rc))
            else:
                dom_ptr = [None]*self._dim
                rel_dom = [""]*self._dim

                for i in range(self._dim):
                    if isinstance(domains[i], GamsSet):
                        dom_ptr[i] = domains[i]._sym_ptr
                    elif isinstance(domains[i], str):
                        rel_dom[i] = domains[i]
                    else:
                        raise gams.control.workspace.GamsException("Domain must be GamsSet or string but saw " + str(type(domains[i])) + " on index " + str(i))
                rc = new_intp()
                self._sym_ptr = gmdAddSymbolXPy(self._database._gmd, self._name, self._dim, dt_set, self._settype, self._text, dom_ptr, rel_dom, rc)
                self._database._check_for_gmd_error(_int_value_and_free(rc))

        else:
            raise gams.control.workspace.GamsException("Invalid combination of parameters")


class GamsEquation(_GamsSymbol):
    '''
    @brief This is the representation of an equation symbol in GAMS.
    @details It exists in a GamsDatabase and contains GamsEquationRecords which one can iterate through.
    '''

    def get_equtype(self):
        return self._equtype
    ## @brief Retrieve subtype of Equation (EquType.E: Equal, EquType.G: Greater, EquType.L: Less, EquType.N: No specification, EquType.X: External defined, EquType.C: Conic)
    equtype = property(get_equtype)

    def __init__(self, database, identifier=None, dimension=None, equtype=None, explanatory_text="", sym_ptr=None, domains=None):
        if identifier and (equtype != None) and (domains != None) and not dimension:
            super(GamsEquation, self).__init__(database, identifier, len(domains), explanatory_text, sym_ptr)
        else:
            super(GamsEquation, self).__init__(database, identifier, dimension, explanatory_text, sym_ptr)
        
        #receive an already existing symbol from GMD
        if not (identifier or dimension or equtype or explanatory_text) and sym_ptr:
            rc, subtype, dval, sval = gmdSymbolInfo(self._database._gmd, self._sym_ptr, GMD_USERINFO)
            self._database._check_for_gmd_error(rc)
            self._equtype = subtype

        #create new equation in GMD
        elif not sym_ptr and identifier and dimension != None and equtype != None:
            self._equtype = equtype
            rc = new_intp()
            self._sym_ptr = gmdAddSymbolPy(self._database._gmd, self._name, self._dim, dt_equ, self._equtype, self._text, rc)
            self._database._check_for_gmd_error(_int_value_and_free(rc))

        #create new equation with domain information
        elif identifier and (equtype != None) and (domains != None) and not dimension:
            if not isinstance(domains, (list, tuple)):
                raise gams.control.workspace.GamsException("Parameter domains has to be a list or a tuple")

            self._equtype = equtype
            if len(domains) == 0:
                rc = new_intp()
                self._sym_ptr = gmdAddSymbolPy(self._database._gmd, self._name, self._dim, dt_equ, self._equtype, self._text, rc);
                self._database._check_for_gmd_error(_int_value_and_free(rc))
            else:
                dom_ptr = [None]*self._dim
                rel_dom = [""]*self._dim

                for i in range(self._dim):
                    if isinstance(domains[i], GamsSet):
                        dom_ptr[i] = domains[i]._sym_ptr
                    elif isinstance(domains[i], str):
                        rel_dom[i] = domains[i]
                    else:
                        raise gams.control.workspace.GamsException("Domain must be GamsSet or string but saw " + str(type(domains[i])) + " on index " + str(i))
                rc = new_intp()
                self._sym_ptr = gmdAddSymbolXPy(self._database._gmd, self._name, self._dim, dt_equ, self._equtype, self._text, dom_ptr, rel_dom, rc)
                self._database._check_for_gmd_error(_int_value_and_free(rc))

        else:
            raise gams.control.workspace.GamsException("Invalid combination of parameters")

class GamsDatabaseDomainViolation(object):
    '''
    @brief This class describes a domain violation of a GamsDatabase.
    '''
    def __init__(self, symbol, dvs):
        self._symbol = symbol
        self._symbol_dvs = dvs

    def _get_symbol(self):
        return self._symbol
    ## @brief GamsSymbol that has a domain violation
    symbol = property(_get_symbol)

    def _get_symbol_dvs(self):
        return self._symbol_dvs
    ## @brief List of domain violations represented by objects of type GamsSymbolDomainViolation
    symbol_dvs = property(_get_symbol_dvs)


class GamsSymbolDomainViolation(object):
    '''
    This class describes a domain violation of a GamsSymbol.
    '''
    def __init__(self, violation_idx, symbol_record):
        self._violation_idx = violation_idx
        self._symbol_record = symbol_record

    def _get_violation_idx(self):
        return self._violation_idx
    ## @brief Array indicating which positions of a record has a domain violation
    violation_idx = property(_get_violation_idx)

    def _get_symbol_record(self):
        return self._symbol_record
    ## @brief GamsSymbolRecord that has a domain violation
    symbol_record = property(_get_symbol_record)

class GamsDatabase(object):
    r'''
    @brief An instance of GamsDatabase communicates data between the Python world and the
           GAMS world.
    @details <p>A GamsDatabase consists of a collection of symbols (GamsDatabase
             implements \__iter__() and next() to allow iterating conveniently
             through the symbols in a GamsDatabase). The symbol types available for a
             GamsDatabase correspond to the symbol types known from the GAMS language: Set,
             Parameter, Variable, and Equation are represented in Python by a derived class
             (e.g. GamsSet, GamsParameter, etc). Besides the type, a GamsSymbol has a name
             (this has to match the name inside the GAMS model), a dimension (currently up to
             20 or GMS_MAX_INDEX_DIM) and some explanatory text.</p>
             <p>Variables and equations also have a subtype: e.g. VarType.Binary, VarType.Positive, etc. for
             variables and e.g. EquType.E, EquType.G etc. for equations</p>
             <p>GamsDatabases can be created empty, or initialized from existing GDX files or
             from another GamsDatabase (copy). Symbols can be added at any time (e.g.
             GamsDatabase.add_parameter), but once a symbol is part of a GamsDatabase, it
             cannot be removed. Only its associated data (GamsSymbolRecord) can be purged
             (see GamsSymbol.clear()) or individually removed (GamsSymbol.delete_record).
             Individual data elements are accessed record by record. A record is identified
             by the keys (a vector of strings). The record data varies by symbol type. For
             example, a parameter record has a value property, a variable has the properties
             level, lower, upper, marginal, and scale. Adding a record with keys that already
             exist results in an exception. Similar, the unsuccessful search for a record
             also results in an exception.</p>
             <p>GamsSymbol implements \__iter__() and next() to conveniently iterate through
             the records of a symbol. There are also sliced access methods to symbol records
             that allow to iterate through all records with a fixed index at some positions.
             GamsDatabases can be exported as GDX files for permanent storage.</p>
             <p>GamsJob.out_db and GamsModelInstance.sync_db provide instances of GamsDatabase
             to communicate results from a GAMS run or a solve. These databases should only
             be used in the context of the base object (GamsJob or GamsModelInstance). If a
             copy of such a database is required GamsWorkspace.add_database can be used to
             initialize a GamsDatabase from another database by specifying the optional parameter
             source_database (e.g. newdb = workspace.add_database(GamsJob.out_db)).</p>
             <p>GamsDatabases often provide the input data for a GamsJob. Such GamsDatabases are
             listed in the GamsJob.run method. Inside the GAMS model source the GamsDatabase
             is accessible through a GDX file. The GAMS model source requires a particular
             file name to connect to the proper GDX file (e.g. $GDXIN filename). A
             GamsDatabase can be created with a given name which can be then used inside the
             model (e.g. db = workspace.add_database(database_name="SupplyData"))
             and then inside the GAMS model source: $GDXIN SupplyData) or an automatically
             generated name can be used. This name can be passed down to the GAMS model by
             using the defines dictionary of a GamsOptions instance:</p>
             @code{.py}
               db = workspace.add_database()
               opt = workspace.add_options()
               opt.defines["SupplyDataFileName"] = db.name
               ...
               gamsjob.run(gams_options=opt, databases=db)
             @endcode
             <p>Inside the GAMS model source the name is accessed as follows:</p>
             @code{.gms}
               $GDXIN %SupplyDataFileName%
             @endcode
             <p>One has to act with some caution when it comes to ordered sets which e.g.
             allow lag and lead. By not enforcing the "domain checking" for the GamsDatabase
             class we have aggravated the potential problems for ordered sets.
             For GAMS, the labels of set elements are just strings, so the order of a set is
             determined by the appearance of its elements. For example, if one has 'set k
             / 2,3,4,1,5 /', the order of k is exactly given by this sequence. So the lag (k-1)
             of k=4 is 3 and the lead (k+1) of k=4 is 1.</p>
             <p>GAMS performs arithmetic with an extended number range. GAMS has special values
             for infinity (+INF, -INF), epsilon (EPS), not available (NA), and undefined (UNDEF).
             When GAMS evaluates expressions with these special values, the calculating engine
             ensures the correctness of the result (e.g. 5*eps=eps or 5+eps=5). The GAMS model
             CRAZY in the GAMS Model Library documents the results of the arithmetic operations
             with respect to special values.</p>
             <p>In the GAMS Python API we map the IEEE standard values for +/-infinity (float('inf')/float('-inf')) and NA (float('nan'))
             to the corresponding GAMS values. The
             special value for UNDEF gets unfiltered through the GAMS Python API. The internal
             double value of UNDEF is 1.0E300 (or better use the constant SV_UNDEF).</p>
             <p>Special attention needs to be given to the value of 0. Since GAMS is a sparse system
             it does not store (parameter) records with a true 0. If a record with numerical value of
             0 is needed, EPS(SV_EPS) can help. For example:</p>
             @code{.gms}
             set j /1*10 /; parameter b(j); b(j) = 1; b('5') = 0;
             scalar s,c; s = sum(j, b(j)); c = card(b); display s,c;
             @endcode
             <p>will result in</p>
             @code{.gms}
             ----      3 PARAMETER s                    =        9.000
                         PARAMETER c                    =        9.000
             @endcode
             <p>but</p>
             @code{.gms}
             b(j) = 1; b('5') = EPS;
             @endcode
             <p>will result in</p>
             @code{.gms}
             ----      3 PARAMETER s                    =        9.000
                         PARAMETER c                    =       10.000
             @endcode
             <p>What are the consequences for the GAMS Python API? If we read parameter b in case of b('5')=0,
             the GAMSDatabase will not have a record for b('5'). In case of b('5')=EPS, the GamsDatabase will
             have a record with value EPS. Unlike the IEEE values (e.g. float("inf")),
             arithmetic operations in Python will modify EPS (e.g. 5*float("inf")==float("inf")
             but 5*EPS!=EPS). The same rules apply for preparing input data for GAMS
             in a GamsDatabase. If a value of EPS is written, GAMS will see the special value EPS.
             All other small values (including 0) will be communicated unfiltered to GAMS. As mentioned before,
             zeros will not be entered as data records in GAMS. The compiler control $on/offEPS can help to
             automatically map zeros to EPS.</p>
             <p>There is one oddity concerning values smaller than 1e-250 on GAMS input. Consider the following example:</p>
             @code{.py}
             b = db.add_parameter("b",1)
             for i in range(1,11):
                 b.add_record(str(i)).value = 1
             b.find_record("5").value = 1E-251
             job.run(db)
             @endcode
             @code{.gms}
             $load j b
             scalar card_b; card_b = card(b); display card_b;
             b(j) = 2*b(j); card_b = card(b); display card_b;
             @endcode
             <p>A record with values smaller than 1e-250 exists on input in GAMS, but as soon as the record gets
             updated by GAMS and is still smaller than 1e-250, the record gets removed.</p>
             <p>The ordering of a set in GAMS can be non-intuitive: Consider "set i /5/, j /1*5/;".
             Elements '5' gets internal number 1, '1' get 2, '2' gets 3 and so on. The last element
             of j '5' has already the internal number 1. The sequence of internal numbers in j is
             not ascending and hence GAMS considers set j as not sorted, i.e. one can't use the
             ord() function nor the lag or lead (-,--,+,++) operators. If 'j' would have been defined
             before 'i' in this example, the "set not ordered" problem would have been avoided.</p>
             <p>Please note that the GamsDatabase actually does not implement a relational model for
             database management. It should be seen as a data storage or data container.</p>
    '''

    #properties
    
    def get_nr_symbols(self):
        ret = gmdInfo(self._gmd, GMD_NRSYMBOLS)
        self._check_for_gmd_error(ret[0])
        return ret[1]
    ## @brief Retrieve the number of symbols in the GamsDatabase
    #  @note This is the same as calling len(database)
    number_symbols = property(get_nr_symbols)

    def get_workspace(self):
        return self._workspace
    ## @brief Get GamsWorkspace containing GamsDatabase
    workspace = property(get_workspace)

    def get_name(self):
        return self._database_name
    ## @brief Get GamsDatabase name
    name = property(get_name)

    def get_suppress_auto_domain_checking(self):
        return self._suppress_auto_domain_checking
    def set_suppress_auto_domain_checking(self, value):
        self._suppress_auto_domain_checking = value
    ## @brief Controls whether domain checking is called in GamsDatabase export
    suppress_auto_domain_checking = property(get_suppress_auto_domain_checking, set_suppress_auto_domain_checking)

    ## @brief Retrieve the number of symbols in the GamsDatabase
    def __len__(self):
        return self.get_nr_symbols()

    def _check_for_gmd_error(self, rc, workspace=None):
        if not rc:
            msg = gmdGetLastError(self._gmd)[1]
            raise gams.control.workspace.GamsException(msg, workspace)

    def __init__(self, ws, database_name=None, gdx_file_name=None, source_database=None, in_model_name=None, force_name=False, gmd_handle=None):
    
        ws._debug_out("---- Entering GamsDatabase constructor ----", 0)
        self._workspace = ws
        self._database_name = None
        if gmd_handle:
            self._gmd = gmd_handle
            self._from_gmd = True
        else:
            self._gmd = new_gmdHandle_tp()
            self._from_gmd = False
        self._record_lock = False
        self._symbol_lock = False
        self._suppress_auto_domain_checking = False
        self._in_model_name = in_model_name

        if not database_name:
            self._database_name = self._workspace._database_add()
        else:
            self._database_name = os.path.splitext(database_name)[0]
            if not self._workspace._database_add(self._database_name) and not force_name:
                raise gams.control.workspace.GamsException("Database with name " + self._database_name + " already exists")
        if not self._from_gmd:
            ret = gmdCreateD(self._gmd, self._workspace._system_directory, GMS_SSSIZE)
            if not ret[0]:
                raise gams.control.workspace.GamsException(ret[1])
            # we need to add the gmd handle to ws in order to free it from the workspace
            ws._gmdHandles.append(self._gmd)
        #set debug mode
        if self._workspace._debug == gams.control.workspace.DebugLevel.Verbose:
            rc = gmdSetDebug(self._gmd, 10)
            self._check_for_gmd_error(rc)
        
        #we have to register our special values first
        if not self._from_gmd:
            if self._workspace._eps != None:
                tmp_spec_values = doubleArray(5)
                tmp_spec_values[0] = _spec_values[0]
                tmp_spec_values[1] = _spec_values[1]
                tmp_spec_values[2] = _spec_values[2]
                tmp_spec_values[3] = _spec_values[3]
                tmp_spec_values[4] = self._workspace._eps
                rc = gmdSetSpecialValues(self._gmd, tmp_spec_values)
            else:
                rc = gmdSetSpecialValues(self._gmd, _spec_values)
            self._check_for_gmd_error(rc)

        #in C# this is separated and is located in another constructor
        if gdx_file_name:
            if str.lower(self._database_name) == str.lower(os.path.splitext(gdx_file_name)[0]) and not force_name:
                raise gams.control.workspace.GamsException("GAMSDatabase name and gdx file name for initialization must be different (saw " + self._database_name + " for both)")

            if os.path.isabs(gdx_file_name):
                rc = gmdInitFromGDX(self._gmd, gdx_file_name)
                self._check_for_gmd_error(rc)
            else:
                rc = gmdInitFromGDX(self._gmd, os.path.join(self._workspace._working_directory, gdx_file_name))
                self._check_for_gmd_error(rc)

        #in C# this is separated and is located in another constructor
        if source_database:
            rc = gmdInitFromDB(self._gmd, gmdHandleToPtr(source_database._gmd))
            self._check_for_gmd_error(rc)

    ## @brief Use this to explicitly free unmanaged resources associated with this GamsDatabase
    def __del__(self):
        self._workspace._debug_out("---- Entering GamsDatabase destructor ----", 0)
        if not self._from_gmd:
            try:
                if self._gmd != None:
                    if gmdHandleToPtr(self._gmd) != None:
                        gmdFree(self._gmd)
            except:
                pass

    def __getitem__(self, symbol_identifier):
        return self.get_symbol(symbol_identifier)

    def __iter__(self):
        self._position = -1
        return self
        
    def next(self):
        self._position+=1
        rc, nr_symbols, dval, sval = gmdInfo(self._gmd, GMD_NRSYMBOLS)
        if not rc:
            raise StopIteration
        if self._position >= nr_symbols:
            raise StopIteration

        rc = new_intp()
        sym_ptr = gmdGetSymbolByIndexPy(self._gmd, self._position+1, rc)
        self._check_for_gmd_error(_int_value_and_free(rc))
        rc, type = gmdSymbolType(self._gmd, sym_ptr)
        self._check_for_gmd_error(rc)

        if type < 0:
            raise gams.control.workspace.GamsException("Cannot retrieve type of symbol")
        if dt_var == type:
            return GamsVariable(self, sym_ptr=sym_ptr)
        if dt_equ == type:
            return GamsEquation(self, sym_ptr=sym_ptr)
        if dt_par == type:
            return GamsParameter(self, sym_ptr=sym_ptr)
        if dt_set == type or dt_alias == type:
            return GamsSet(self, sym_ptr=sym_ptr)
        raise gams.control.workspace.GamsException("Unknown symbol type " + str(type))

    def __next__(self):
        return self.next()

    def get_symbol(self, symbol_identifier):
        '''
        @brief Get GamsSymbol by name
        @details
        @code{.py}
        symbol = database.get_symbol("a")
        if isinstance(symbol, GamsParameter):
            print("symbol is a GamsParameter")
        if isinstance(symbol, GamsSet):
            print("symbol is a GamsSet")
        if isinstance(symbol, GamsVariable):
            print("symbol is a GamsVariable")
        if isinstance(symbol, GamsEquation):
            print("symbol is a GamsEquation")
        @endcode
        @param symbol_identifier Name of the symbol to retrieve
        @return Instance of _GamsSymbol
        @see get_parameter(), get_set(). get_variable(), get_equation()
        '''
        rc = new_intp()
        sym_ptr = gmdFindSymbolPy(self._gmd, symbol_identifier, rc)
        self._check_for_gmd_error(_int_value_and_free(rc))
        rc, type = gmdSymbolType(self._gmd, sym_ptr)
        self._check_for_gmd_error(rc)

        #implement this as a dictionary to provide switch-like behavior like in C#
        if type == dt_equ:
            return self.get_equation(symbol_identifier)
        elif type == dt_var:
            return self.get_variable(symbol_identifier);
        elif type == dt_par:
            return self.get_parameter(symbol_identifier);
        elif type == dt_set:
            return self.get_set(symbol_identifier);
        elif type == dt_alias:
            return self.get_set(symbol_identifier);
        else:
            raise gams.control.workspace.GamsException("Unknown symbol type " + str(type));

    def get_equation(self, equation_identifier):
        '''
        @brief Get GamsEquation by name
        @param equation_identifier Name of the equation to retrieve
        @return Instance of GamsEquation
        @see get_symbol(), get_parameter(), get_set(), get_variable()
        '''
        rc = new_intp()
        sym_ptr = gmdFindSymbolPy(self._gmd, equation_identifier, rc)
        self._check_for_gmd_error(_int_value_and_free(rc))
        rc, type = gmdSymbolType(self._gmd, sym_ptr)
        self._check_for_gmd_error(rc)
        if type != dt_equ:
            raise gams.control.workspace.GamsException("GamsDatabase: Symbol " + equation_identifier + " is not an equation")
        return GamsEquation(self, sym_ptr=sym_ptr)

    def get_parameter(self, parameter_identifier):
        '''
        @brief Get GamsParameter by name
        @param parameter_identifier Name of the parameter to retrieve
        @return Instance of GamsParameter
        @see get_symbol(), get_set(), get_variable(), get_equation()
        '''
        rc = new_intp()
        sym_ptr = gmdFindSymbolPy(self._gmd, parameter_identifier, rc)
        self._check_for_gmd_error(_int_value_and_free(rc))
        rc, type = gmdSymbolType(self._gmd, sym_ptr)
        self._check_for_gmd_error(rc)
        if type != dt_par:
            raise gams.control.workspace.GamsException("GamsDatabase: Symbol " + parameter_identifier + " is not a parameter")
        return GamsParameter(self, sym_ptr=sym_ptr)

    def get_variable(self, variable_identifier):
        '''
        @brief Get GamsVariable by name
        @param variable_identifier Name of the variable to retrieve
        @return Instance of GamsVariable
        @see get_symbol(), get_parameter(), get_set(), get_equation()
        '''
        rc = new_intp()
        sym_ptr = gmdFindSymbolPy(self._gmd, variable_identifier, rc)
        self._check_for_gmd_error(_int_value_and_free(rc))
        rc, type = gmdSymbolType(self._gmd, sym_ptr)
        self._check_for_gmd_error(rc)
        if type != dt_var:
            raise gams.control.workspace.GamsException("GamsDatabase: Symbol " + variable_identifier + " is not a variable")
        return GamsVariable(self, sym_ptr=sym_ptr)

    def get_set(self, set_identifier):
        '''
        @brief Get GamsSet by name
        @param set_identifier Name of the set to retrieve
        @return Instance of GamsSet
        @see get_symbol(), get_parameter(), get_variable(), get_equation()
        '''
        rc = new_intp()
        sym_ptr = gmdFindSymbolPy(self._gmd, set_identifier, rc)
        self._check_for_gmd_error(_int_value_and_free(rc))
        rc, type = gmdSymbolType(self._gmd, sym_ptr)
        if type != dt_set and type != dt_alias:
            raise gams.control.workspace.GamsException("GamsDatabase: Symbol " + set_identifier + " is not a set")
        return GamsSet(self, sym_ptr=sym_ptr)

    def add_equation(self, identifier, dimension, equtype, explanatory_text=""):
        '''
        @brief Add equation symbol to database
        @param identifier Equation name
        @param dimension Equation dimension
        @param equtype Equation subtype (EquType.E: Equal, EquType.G: Greater, EquType.L: Less, EquType.N: No specification, EquType.X: External defined, EquType.C: Conic)
        @param explanatory_text Explanatory text of equation
        @return Instance of GamsEquation        
        @see add_parameter(), add_set(), add_variable()
        '''
        if self._symbol_lock:
            raise gams.control.workspace.GamsException("Cannot add symbols to symbol-locked database")
        return GamsEquation(self, identifier, dimension, equtype, explanatory_text)

    def add_equation_dc(self, identifier, equtype, domains, explanatory_text=""):
        '''
        @brief Add equation symbol to database using domain information
        @param identifier Equation name
        @param equtype Equation subtype (EquType.E: Equal, EquType.G: Greater, EquType.L: Less, EquType.N: No specification, EquType.X: External defined, EquType.C: Conic)
        @param domains A list containing GamsSet objects and strings for domain information. The length of the list specifies the dimension.
        @param explanatory_text Explanatory text of equation
        @return Instance of GamsEquation
        @see add_parameter_dc(), add_set_dc(), add_variable_dc()
        '''
        if self._symbol_lock:
            raise gams.control.workspace.GamsException("Cannot add symbols to symbol-locked database")
        if domains == None:
            domains = []
        return GamsEquation(self, identifier, None, equtype, explanatory_text, domains=domains)

    def add_variable(self, identifier, dimension, vartype, explanatory_text=""):
        '''
        @brief Add variable symbol to database
        @param identifier Variable name
        @param dimension Variable dimension
        @param vartype Variable subtype (VarType.Binary, VarType.Integer, VarType.Positive, VarType.Negative, VarType.Free, VarType.SOS1, VarType.SOS2, VarType.SemiCont, VarType.SemiInt)
        @param explanatory_text Explanatory text to variable
        @return Instance of GamsVariable
        @see add_equation(), add_parameter(), add_set()
        '''
        if self._symbol_lock:
            raise gams.control.workspace.GamsException("Cannot add symbols to symbol-locked database")
        return GamsVariable(self, identifier, dimension, vartype, explanatory_text)

    def add_variable_dc(self, identifier, vartype, domains, explanatory_text=""):
        '''
        @brief Add variable symbol to database using domain information
        @param identifier Variable name
        @param vartype Variable subtype (VarType.Binary, VarType.Integer, VarType.Positive, VarType.Negative, VarType.Free, VarType.SOS1, VarType.SOS2, VarType.SemiCont, VarType.SemiInt)
        @param domains A list containing GamsSet objects and strings for domain information. The length of the list specifies the dimension.
        @param explanatory_text Explanatory text to variable
        @return Instance of GamsVariable
        @see add_equation_dc(), add_parameter_dc(), add_set_dc()
        '''
        if self._symbol_lock:
            raise gams.control.workspace.GamsException("Cannot add symbols to symbol-locked database")
        if domains == None:
            domains = []
        return GamsVariable(self, identifier, None, vartype, explanatory_text, domains=domains)

    def add_set(self, identifier, dimension, explanatory_text="", settype=0):
        '''
        @brief Add set symbol to database
        @param identifier Set name
        @param dimension Set dimension
        @param explanatory_text Explanatory text of set
        @param settype Set subtype (SetType.Multi, SetType.Singleton)
        @return Instance of GamsSet
        @see add_equation(), add_parameter(), add_variable()
        '''
        if self._symbol_lock:
            raise gams.control.workspace.GamsException("Cannot add symbols to symbol-locked database")
        return GamsSet(self, identifier, dimension, explanatory_text, settype = settype)

    def add_set_dc(self, identifier, domains, explanatory_text="", settype=0):
        '''
        @brief Add set symbol to database using domain information
        @param identifier Set name
        @param domains A list containing GamsSet objects and strings for domain information. The length of the list specifies the dimension.
        @param explanatory_text Explanatory text of set
        @param settype Set subtype (SetType.Multi, SetType.Singleton)
        @return Instance of GamsSet        
        @see add_equation_dc(), add_parameter_dc(), add_variable_dc()
        '''
        if self._symbol_lock:
            raise gams.control.workspace.GamsException("Cannot add symbols to symbol-locked database")
        if domains == None or len(domains) == 0:
            domains = ["*"]
        return GamsSet(self, identifier, None, explanatory_text, domains=domains, settype = settype)

    def add_parameter(self, identifier, dimension, explanatory_text=""):
        '''
        @brief Add parameter symbol to database
        @param identifier Parameter name
        @param dimension Parameter dimension
        @param explanatory_text Explanatory text of parameter
        @return Instance of GamsParameter
        @see add_equation(), add_set(), add_variable()
        '''
        if self._symbol_lock:
            raise gams.control.workspace.GamsException("Cannot add symbols to symbol-locked database")
        return GamsParameter(self, identifier, dimension, explanatory_text)

    def add_parameter_dc(self, identifier, domains, explanatory_text=""):
        '''
        @brief Add parameter symbol to database using domain information
        @param identifier Parameter name
        @param domains A list containing GamsSet objects and strings for domain information. The length of the list specifies the dimension.
        @param explanatory_text Explanatory text of parameter
        @return Instance of GamsParameter
        @see add_equation_dc(), add_set_dc(), add_variable_dc()
        '''
        if self._symbol_lock:
            raise gams.control.workspace.GamsException("Cannot add symbols to symbol-locked database")
        if domains == None:
            domains = []
        return GamsParameter(self, identifier, None, explanatory_text, domains=domains)

    def export(self, file_path=None):
        '''
        @brief Write database into a GDX file
        @param file_path The path used to write the GDX file.
               A relative path is relative to the GAMS working directory.
               If not present, the file is written to the working directory using the name of the database.
        '''
        if not self._suppress_auto_domain_checking:
            if not self.check_domains():
                raise gams.control.workspace.GamsException("Domain violations in GamsDatabase " + self._database_name)

        if not file_path:
            rc = gmdWriteGDX(self._gmd, os.path.join(self._workspace._working_directory, self._database_name + ".gdx"), self._suppress_auto_domain_checking)
            self._check_for_gmd_error(rc)
        else:
            file_path = os.path.splitext(file_path)[0] + ".gdx"
            if os.path.isabs(file_path):
                rc = gmdWriteGDX(self._gmd, file_path, self._suppress_auto_domain_checking);
            else:
                rc = gmdWriteGDX(self._gmd, os.path.join(self._workspace._working_directory, file_path), self._suppress_auto_domain_checking)
            self._check_for_gmd_error(rc)

    def clear(self):
        '''
        @brief Clear all symbols in GamsDatabase
        '''
        for symbol in self:
            if not symbol.clear():
                raise gams.control.workspace.GamsException("Cannot clear symbol " + symbol._name)

    def compact(self):
        '''
        @brief This function is obsolete and has no effect anymore. It will be removed in the future
        '''
        #gmdFreeAllSymbolIterators(self._gmd)

    def check_domains(self):
        '''
        @brief Check for all symbols if all records are within the specified domain of the symbol
        @return True: Everything is correct, False: There is a domain violation
        '''
        has_violation = new_intp()
        rc = gmdCheckDBDV(self._gmd, has_violation)
        self._check_for_gmd_error(rc)
        if _int_value_and_free(has_violation) == 1:
            return False
        else:
            return True

    def get_database_dvs(self, max_viol = 0, max_viol_per_symbol = 0):
        '''
        @brief return all GamsDatabaseDomainViolations
        @param max_viol The maximum number of domain violations which should be stored (0 for no limit)
        @param max_viol_per_symbol The maximum number of domain violations which should be stored per Symbol (0 for no limit)
        @return List containing GamsDatabaseDomainViolation objects
        '''
        rc = new_intp()
        ret_list = []
        nr_viols = 0
        dv_handle = gmdGetFirstDBDVPy(self._gmd, rc)
        self._check_for_gmd_error(_int_value_and_free(rc))

        has_next_db = False
        if dv_handle != None:
            has_next = True
            has_next_db =  True

        while has_next_db and (nr_viols < max_viol or max_viol == 0):
            current_symbol_dvs = []
            rc = new_intp()
            current_symbol_ptr = gmdGetDVSymbolPy(self._gmd, dv_handle, rc)
            self._check_for_gmd_error(_int_value_and_free(rc))

            ret = gmdSymbolInfo(self._gmd, current_symbol_ptr, GMD_DIM)
            self._check_for_gmd_error(ret[0])
            dim = ret[1]
            rc, type = gmdSymbolType(self._gmd, current_symbol_ptr)
            self._check_for_gmd_error(rc)
            current_symbol = None
            if type == dt_equ:
                current_symbol = GamsEquation(self, sym_ptr = current_symbol_ptr)
            elif type == dt_var:
                current_symbol = GamsVariable(self, sym_ptr = current_symbol_ptr)
            elif type == dt_par:
                current_symbol = GamsParameter(self, sym_ptr = current_symbol_ptr)
            elif type == dt_set:
                current_symbol = GamsSet(self, sym_ptr = current_symbol_ptr)

            while has_next and (len(current_symbol_dvs) < max_viol_per_symbol or max_viol_per_symbol == 0) and (nr_viols < max_viol or max_viol == 0):
                rc = new_intp()
                rec = gmdGetDVSymbolRecordPy (self._gmd, dv_handle, rc)
                self._check_for_gmd_error(_int_value_and_free(rc))

                violation_idx = intArray(dim)
                rc = gmdGetDVIndicator (self._gmd, dv_handle, violation_idx)
                self._check_for_gmd_error(rc)

                violation_idx_list = []
                for i in range(dim):
                    violation_idx_list.append(bool(violation_idx[i]))

                rc, type = gmdSymbolType(self._gmd, current_symbol_ptr)
                self._check_for_gmd_error(rc)
                symbol_record = None
                if type == dt_equ:
                    symbol_record = GamsEquationRecord(current_symbol, rec)
                elif type == dt_var:
                    symbol_record = GamsVariableRecord(current_symbol, rec)
                elif type == dt_par:
                    symbol_record = GamsParameterRecord(current_symbol, rec)
                elif type == dt_set:
                    symbol_record = GamsSetRecord(current_symbol, rec)

                current_symbol_dvs.append( GamsSymbolDomainViolation(violation_idx_list, symbol_record) )
                nr_viols += 1
                has_next = new_intp()
                rc = gmdMoveNextDVInSymbol(self._gmd, dv_handle, has_next)
                self._check_for_gmd_error(rc)
                has_next = bool(_int_value_and_free(has_next))

            has_next_db = new_intp()
            rc = gmdGetFirstDVInNextSymbol(self._gmd, dv_handle, has_next_db)
            self._check_for_gmd_error(rc)
            has_next_db = bool(_int_value_and_free(has_next_db))
            has_next = has_next_db

            ret_list.append(GamsDatabaseDomainViolation(current_symbol, current_symbol_dvs))

        rc = gmdDomainCheckDone(self._gmd)
        self._check_for_gmd_error(rc)
        rc = gmdFreeDVHandle(self._gmd, dv_handle)
        self._check_for_gmd_error(rc)

        return ret_list
