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
# This file was generated.

from gams.core.gmo import *
from gams.core.cfg import *
from gams.core.opt import *
import gams.control.workspace
import os
import tempfile
import sys

## @brief GAMS processing request
class Action(object):
    ## @brief Restart After Solve
    RestartAfterSolve = "R"
    ## @brief CompileOnly
    CompileOnly = "C"
    ## @brief ExecuteOnly
    ExecuteOnly = "E"
    ## @brief Compile and Execute
    CompileAndExecute = "CE"
    ## @brief Glue Code Generation
    GlueCodeGeneration = "G"
    ## @brief Trace Report
    TraceReport = "GT"

## @brief Expand file append option
class AppendExpand(object):
    ## @brief Reset expand file
    Reset = 0
    ## @brief Append to expand file
    Append = 1

## @brief Output file append option
class AppendOut(object):
    ## @brief Reset listing file
    Reset = 0
    ## @brief Append to listing file
    Append = 1

## @brief Print solution listing when asynchronous solve (Grid or Threads) is used
class AsyncSolLst(object):
    ## @brief Do not print solution listing into lst file for asynchronous solves
    Off = 0
    ## @brief Print solution listing into lst file for asynchronous solves
    On = 1

## @brief Switch to capture all model instances within a run
class CaptureModelInstance(object):
    ## @brief Do not capture model instances
    Off = 0
    ## @brief Capture model instances
    On = 1

## @brief Output case option for LST file
class Case(object):
    ## @brief Write listing file in mixed case
    MixedCase = 0
    ## @brief Write listing file in upper case only
    UpperCase = 1

## @brief Character set flag
class CharSet(object):
    ## @brief Use limited GAMS characters set
    LimitedGAMSCharSet = 0
    ## @brief Accept any character in comments and text items (foreign language characters)
    AnyChar = 1

## @brief Check errorLevel automatically after executing external program
class CheckErrorLevel(object):
    ## @brief Do not check errorLevel automatically after execution of external program
    Off = 0
    ## @brief Check errorLevel automatically after execution of external program
    On = 1

## @brief Date format
class DFormat(object):
    ## @brief Date as mm/dd/yy
    Slash = 0
    ## @brief Date as dd.mm.yy
    Dot = 1
    ## @brief Date as yy-mm-dy
    Dash = 2

## @brief Switch default for "$on/offDigit"
class Digit(object):
    ## @brief Activate $offDigit
    OffDigit = "off"
    ## @brief Activate $onDigit
    OnDigit = "on"

## @brief Writes preprocessed input to the file input.dmp
class DumpOpt(object):
    ## @brief No dumpfile
    No = 0
    ## @brief Extract referenced data from the restart file using original set element names
    RefDataOriginalSetElementNames = 1
    ## @brief Extract referenced data from the restart file using new set element names
    RefDataNewSetElementNames = 2
    ## @brief Extract referenced data from the restart file using new set element names and drop symbol text
    RefDataNewSetElementNamesDropSymbolText = 3
    ## @brief Extract referenced symbol declarations from the restart file
    RefSymbol = 4
    ## @brief (Same as 11 and therefore hidden)
    Deprecated_10 = 10
    ## @brief Write processed input file without comments
    InputFileWOComments = 11
    ## @brief (Same as 11 and therefore hidden)
    Deprecated_12 = 12
    ## @brief (Same as 21 and therefore hidden)
    Deprecated_19 = 19
    ## @brief (Same as 21 and therefore hidden)
    Deprecated_20 = 20
    ## @brief Write processed input file with all comments
    InputFileWithComments = 21
    ## @brief Write processed input with all comments into a separate dump file for each block
    SplitBlocksDumpWithComments = 22

## @brief GAMS parameter logging
class DumpParms(object):
    ## @brief No logging
    No = 0
    ## @brief Lists accepted/set parameters
    AcceptedParameters = 1
    ## @brief Log of file operations plus list of accepted/set parameters
    FileOperationsAcceptedParameters = 2

## @brief Allow implicit loading of symbols from embedded code or not
class ECImplicitLoad(object):
    ## @brief Do not allow implicit loading from embedded code
    OffECImplicitLoad = "off"
    ## @brief Allow implicit loading from embedded code
    OnECImplicitLoad = "on"

## @brief Switch default for "$on/offEmpty"
class Empty(object):
    ## @brief Activate $offEmpty
    OffEmpty = "off"
    ## @brief Activate $onEmpty
    OnEmpty = "on"

## @brief Placing of compilation error messages
class ErrMsg(object):
    ## @brief Place error messages at the end of compiler listing
    EndOfCompilerListing = 0
    ## @brief Place error messages immediately following the line with the error
    FollowingError = 1
    ## @brief Suppress error messages
    Suppress = 2

## @brief Limits on external programs that are allowed to be executed
class ExecMode(object):
    ## @brief Everything allowed
    EverythingAllowed = 0
    ## @brief Interactive shells in $call and execute commands are prohibited
    InteractiveShellsProhibited = 1
    ## @brief Embedded Code and all $call and execute commands are prohibited
    CallAndExecuteProhibited = 2
    ## @brief $echo or put commands can only write to directories in or below the working or scratchdir
    EchoAndPutOnlyToWorkdir = 3
    ## @brief $echo and put commands are not allowed
    EchoAndPutProhibited = 4

## @brief Options for finite differences
class FDOpt(object):
    ## @brief All derivatives analytically, for numerical Hessian use gradient values, scale delta
    GHAnalyticHNumericGradScale = 0
    ## @brief All derivatives analytically, for numerical Hessian use function values, scale delta
    GHAnalyticHNumericFuncScale = 1
    ## @brief Gradient analytically, force Hessian numerically using gradient values, scale delta
    GAnalyticFHNumericGradScale = 2
    ## @brief Gradient analytically, force Hessian numerically using function values, scale delta
    GAnalyticFHNumericFuncScale = 3
    ## @brief Force gradient and Hessian numerically, scale delta
    FGHNumericScale = 4
    ## @brief Same as 0, but no scale of delta
    GHAnalyticHNumericGradNoScale = 10
    ## @brief Same as 1, but no scale of delta
    GHAnalyticHNumericFuncNoScale = 11
    ## @brief Same as 2, but no scale of delta
    GAnalyticFHNumericGradNoScale = 12
    ## @brief Same as 3, but no scale of delta
    GAnalyticFHNumericFuncNoScale = 13
    ## @brief Same as 4, but no scale of delta
    FGHNumericNoScale = 14

## @brief Casing of file names and paths (put, gdx, ref, $include, etc.)
class FileCase(object):
    ## @brief Causes GAMS to use default casing
    DefaultCase = 0
    ## @brief Causes GAMS to upper case file names including path of the file
    UpperCase = 1
    ## @brief Causes GAMS to lower case file names including path of the file
    LowerCase = 2
    ## @brief Causes GAMS to upper case file names only (leave the path alone)
    UpperCaseFileOnly = 3
    ## @brief Causes GAMS to lower case file names only (leave the path alone)
    LowerCaseFileOnly = 4

## @brief Switch between filtered and domain-checked read from GDX
class Filtered(object):
    ## @brief Load domain checked
    OffFiltered = "off"
    ## @brief Load filtered
    OnFiltered = "on"

## @brief Force GAMS to process a save file created with a newer GAMS version or with execution errors
class ForceWork(object):
    ## @brief No translation
    NoTranslation = 0
    ## @brief Try translation
    TryTranslation = 1

## @brief Free external resources at the end of each embedded Python code blocks
class FreeEmbeddedPython(object):
    ## @brief Keep resources to reuse them potentially
    Off = 0
    ## @brief Free resources
    On = 1

## @brief Compression of generated GDX file
class gdxCompress(object):
    ## @brief Do not compress GDX files
    DoNotCompressGDX = 0
    ## @brief Compress GDX files
    CompressGDX = 1

## @brief Version of GDX files generated (for backward compatibility)
class gdxConvert(object):
    ## @brief Version 5 GDX file, does not support compression
    Version5 = "v5"
    ## @brief Version 6 GDX file
    Version6 = "v6"
    ## @brief Version 7 GDX file
    Version7 = "v7"

## @brief Unload labels or UELs to GDX either squeezed or full
class gdxUels(object):
    ## @brief Write only the UELs to Universe, that are used by the exported symbols
    squeezed = "Squeezed"
    ## @brief Write all UELs to Universe
    full = "Full"

## @brief Treat fixed variables as constants
class HoldFixed(object):
    ## @brief Fixed variables are not treated as constants
    FixedVarsNotTreatedAsConstants = 0
    ## @brief Fixed variables are treated as constants
    FixedVarsTreatedAsConstants = 1

## @brief Allow HoldFixed for models solved asynchronously as well
class HoldFixedAsync(object):
    ## @brief Ignore HoldFixed setting for async solves
    Off = 0
    ## @brief Allow HoldFixed for async solves
    On = 1

## @brief Switch default for "$on/offImplicitAssign"
class ImplicitAssign(object):
    ## @brief Activate $offImplicitAssign
    OffImplicitAssign = "off"
    ## @brief Activate $onImplicitAssign
    OnImplicitAssign = "on"

## @brief Allow solver to interact via command line input
class InteractiveSolver(object):
    ## @brief Interaction with solvelink 0 is not supported
    NoInteraction = 0
    ## @brief Interaction with solvelink 0 is supported
    AllowInteraction = 1

## @brief Set mode for default upper bounds on integer variables
class IntVarUp(object):
    ## @brief Set default upper bound for integer variables to +INF
    INF = 0
    ## @brief Pass a value of 100 instead of +INF to the solver as upper bound for integer variables
    Pass100ToSolver = 1
    ## @brief Same as 0 but writes a message to the log if the level of an integer variable is greater than 100
    INFandLog = 2
    ## @brief Same as 2 but issues an execution error if the level of an integer variable is greater than 100
    Pass100ToSolverAndError = 3

## @brief Controls keeping or deletion of process directory and scratch files
class Keep(object):
    ## @brief Delete process directory
    DeleteProcDir = 0
    ## @brief Keep process directory
    KeepProcDir = 1

## @brief Switch default for "$on/offListing"
class Listing(object):
    ## @brief Activate $offListing
    OffListing = "off"
    ## @brief Activate $onListing
    OnListing = "on"

## @brief Amount of line tracing to the log file
class LogLine(object):
    ## @brief No line tracing
    NoTracing = 0
    ## @brief Minimum line tracing
    MinimumTracing = 1
    ## @brief Automatic and visually pleasing
    Automatic = 2

## @brief Write title of LST file all left aligned
class LstTitleLeftAligned(object):
    ## @brief Split LST title into left and right aligned part
    Off = 0
    ## @brief Write LST title completely left aligned
    On = 1

## @brief Model Instance Mode
class MIIMode(object):
    ## @brief Default behavior
    Off = "off"
    ## @brief Setup to inspect a single model instance
    SingleMI = "singleMI"
    ## @brief Setup to inspect multiple model instances from one model
    MultiMI = "multiMI"

## @brief Triggers a compilation error when new equations or variable symbols are introduced
class NoNewVarEqu(object):
    ## @brief AllowNewVarEqu
    AllowNewVarEqu = 0
    ## @brief DoNotAllowNewVarEqu
    DoNotAllowNewVarEqu = 1

## @brief Generate errors for unknown unique element in an equation
class On115(object):
    ## @brief No error messages
    NoMessages = 0
    ## @brief Issue error messages
    IssueMessages = 1

## @brief Output file page control option
class PageContr(object):
    ## @brief No page control, with padding
    NoPageContrWithPadding = 0
    ## @brief FORTRAN style line printer format
    FortranStyle = 1
    ## @brief No page control, no padding
    NoPageContrNoPadding = 2
    ## @brief Formfeed character for new page
    FormfeedCharNewPage = 3

## @brief Prepend GAMS system directory to library load path
class PrefixLoadPath(object):
    ## @brief Do not set GAMS system directory at beginning of library load path
    Off = 0
    ## @brief Set GAMS system directory at beginning of library load path
    On = 1

## @brief Indicator for writing workfile with previous workfile version
class PreviousWork(object):
    ## @brief Write workfile using the current version
    Off = 0
    ## @brief Write workfile using the previous workfile version
    On = 1

## @brief Monitor the memory used by the GAMS process tree
class ProcTreeMemMonitor(object):
    ## @brief Do not monitor memory usage for the GAMS process tree
    Off = 0
    ## @brief Start a thread to monitor memory usage for the GAMS process tree
    On = 1

## @brief Numeric round format for put files
class PutNR(object):
    ## @brief Item is displayed in F or E format
    ForE = 0
    ## @brief Item is rounded to fit given width and decimals
    Rounded = 1
    ## @brief Item is displayed in scientific notation
    Scientific = 2
    ## @brief Item is rounded to fit given width
    RoundedFloatingDec = 3
    ## @brief Item is displayed in F or E format ignoring given decimals
    ForEFloatingDec = 4

## @brief Controls the line numbers written to a reference file
class ReferenceLineNo(object):
    ## @brief Actual line number of symbol reference
    ActualLineNumber = "actual"
    ## @brief Line number where the statement with the reference starts
    StatementStart = "start"

## @brief Switch between merge and replace when reading from GDX into non-empty symbol
class Replace(object):
    ## @brief Merge into existing data when loading
    Merge = "off"
    ## @brief Replace existing data when loading
    Replace = "on"

## @brief Save solver point in GDX file
class SavePoint(object):
    ## @brief No point GDX file is to be saved
    NoPointFile = 0
    ## @brief A point GDX file from the last solve is to be saved
    LastSolvePointFile = 1
    ## @brief A point GDX file from every solve is to be saved
    EverySolvePointFile = 2
    ## @brief A point GDX file from the last solve is to be saved in the scratch directory
    LastSolvePointFileScrDir = 3
    ## @brief A point GDX file from every solve is to be saved in the scratch directory
    EverySolvePointFileScrDir = 4

## @brief Show the memory usage reported by the Operating System instead of the internal counting
class ShowOSMemory(object):
    ## @brief Show memory reported by internal accounting
    InternalAccounting = 0
    ## @brief Show resident set size reported by operating system
    RSS = 1
    ## @brief Show virtual set size reported by operating system
    VSS = 2

## @brief Solution report print option
class SolPrint(object):
    ## @brief Remove solution listings following solves
    RemoveSolLstFollowingSolves = 0
    ## @brief Include solution listings following solves
    IncludeSolLstFollowingSolves = 1
    ## @brief Suppress all solution information
    SuppressAllSolInfo = 2

## @brief Solver link option
class SolveLink(object):
    ## @brief Model instance and entire GAMS state saved to scratch directory, GAMS exits (and vacates memory), and the solver script is called. After the solver terminates, GAMS restarts from the saved state and continues to executing
    ChainScript = 0
    ## @brief Model instance saved to scratch directory, the solver is called from a shell while GAMS remains open
    CallScript = 1
    ## @brief Model instance saved to scratch directory, the solver is called with a spawn (if possible) or a shell (if spawn is not possible) while GAMS remains open - If this is not supported by the selected solver, it gets reset to `1` automatically
    CallModule = 2
    ## @brief Model instance saved to scratch directory, the solver starts the solution and GAMS continues
    AsyncGrid = 3
    ## @brief Model instance saved to scratch directory, the solver starts the solution and GAMS waits for the solver to come back but uses same submission process as 3 (test mode)
    AsyncSimulate = 4
    ## @brief The model instance is passed to the solver in-memory - If this is not supported by the selected solver, it gets reset to `2` automatically
    LoadLibrary = 5
    ## @brief The model instance is passed to the solver in-memory, the solver starts the solution and GAMS continues
    LoadLibraryAsync = 6
    ## @brief The model instance is passed to the solver in-memory, the solver starts the solution and GAMS waits for the solver to come back but uses same submission process as 6 (test mode)
    LoadLibraryAsyncSimulate = 7

## @brief Multiple solve management
class SolveOpt(object):
    ## @brief The solution information for all equations appearing in the model is completely replaced by the new model results; variables are only replaced if they appear in the final model
    Merge = 0
    ## @brief The solution information for all equations and variables is merged into the existing solution information
    Replace = 1
    ## @brief The solution information for all equations appearing in the model is completely replaced; in addition, variables appearing in the symbolic equations but removed by conditionals will be removed
    Clear = 2

## @brief Summary of computing resources used by job steps
class StepSum(object):
    ## @brief No step summary
    NoStepSummmary = 0
    ## @brief Step summary printed
    StepSummary = 1

## @brief Error if assignment to singleton set has multiple elements
class strictSingleton(object):
    ## @brief Take first record if assignment to singleton set has multiple elements
    FirstRecord = 0
    ## @brief Error if assignment to singleton set has multiple elements
    Error = 1

## @brief String substitution options
class StringChk(object):
    ## @brief No substitution if symbol undefined and no error
    NoError = 0
    ## @brief Error if symbol undefined
    Error = 1
    ## @brief Remove entire symbol reference if undefined and no error
    NoErrorRemoveSymbol = 2

## @brief Switch default for "$on/offSuffixDLVars"
class SuffixDLVars(object):
    ## @brief Activate $offSuffixDLVars
    OffSuffixDLVars = "off"
    ## @brief Activate $onSuffixDLVars
    OnSuffixDLVars = "on"

## @brief Switch default for "$on/offSuffixAlgebraVars"
class SuffixAlgebraVars(object):
    ## @brief Activate $offSuffixAlgebraVars
    OffSuffixAlgebraVars = "off"
    ## @brief Activate $onSuffixAlgebraVars
    OnSuffixAlgebraVars = "on"

## @brief Compiler listing option
class Suppress(object):
    ## @brief Standard compiler listing
    StandardCompilerListing = 0
    ## @brief Suppress compiler listing
    SuppressCompilerListing = 1

## @brief Changes rpower to ipower when the exponent is constant and within 1e-12 of an integer
class Sys10(object):
    ## @brief Disable conversion
    Disable = 0
    ## @brief Enable conversion
    Enable = 1

## @brief Dynamic resorting if indices in assignment/data statements are not in natural order
class Sys11(object):
    ## @brief Automatic optimization/restructuring of data
    AutomaticOptimization = 0
    ## @brief No optimization
    NoOptimization = 1
    ## @brief Always optimize/restructure
    AlwaysOptimize = 2

## @brief Solver Status file reporting option
class SysOut(object):
    ## @brief Suppress additional solver generated output
    SuppressAdditionalSolverOutput = 0
    ## @brief Include additional solver generated output
    IncludeAdditionalSolverOutput = 1

## @brief Time format
class TFormat(object):
    ## @brief Time as hh:mm:ss
    Colon = 0
    ## @brief Time as hh.mm.ss
    Dot = 1

## @brief Trace file format option
class TraceOpt(object):
    ## @brief Solver and GAMS step trace
    SolverAndGAMSStepTraceWOHeaders = 0
    ## @brief Solver and GAMS exit trace
    SolverAndGAMSStepTrace = 1
    ## @brief Solver trace only
    SolverStepTraceOnly = 2
    ## @brief Solver trace only in format used for GAMS performance world
    TraceFileFormatGAMSPerformanceWorld = 3
    ## @brief Trace file format supporting NLPEC
    TraceFileFormatSupportingNLPEC = 4
    ## @brief Gams exit trace with all available trace fields
    TraceFileWithAllAvailableTraceFields = 5

## @brief Report underflow as a warning when abs(results) LE ZeroRes and result set to zero
class ZeroResRep(object):
    ## @brief No warning when a rounding occurs because of ZeroRes
    NoWarning = 0
    ## @brief Issue warnings whenever a rounding occurs because of ZeroRes
    IssueWarning = 1

import threading

class GamsOptions(object):
    '''
    @brief The GamsOptions class manages GAMS options (sometimes also called GAMS
           parameters since they correspond to the command line parameters of the GAMS
           executable) for a GamsJob and GamsModelInstance.
    @details <p>There are integer (e.g. nodlim), double (e.g. reslim), and string (e.g. putdir)
             valued options. There are also a few list options (defines to set string macros inside
             GAMS and idir provide multiple search paths for include files) and a power option to set a
             solver for all suitable model types (all_model_types).</p>
             <p>Some options known from other interfaces to GAMS that are of limited use or
             could even create problematic situations in the Python environment are not
             settable through the GamsOptions class.</p>
             @todo{adjust this paragraph to python specifics}
             <p>For some options (e.g. case) other GAMS interfaces use numeric values (e.g. 0,1)
             while the GamsOptions class has enumerated types with proper names (e.g.
             MixedCase, UpperCase).</p>
    '''
    optLock = threading.Lock()

    def set_all_model_types(self, value):
        for i in range(1, gmoProc_nrofmodeltypes):
            if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), i):
                self._selected_solvers[i] = value
    ## @brief Set solver for all model types
    all_model_types = property(fset=set_all_model_types)

    def get_lp(self):
        return self._selected_solvers[gmoProc_lp]
    def set_lp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_lp):
            self._selected_solvers[gmoProc_lp] = value
    ## @brief Default lp solver
    lp = property(get_lp, set_lp)

    def get_mip(self):
        return self._selected_solvers[gmoProc_mip]
    def set_mip(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_mip):
            self._selected_solvers[gmoProc_mip] = value
    ## @brief Default mip solver
    mip = property(get_mip, set_mip)

    def get_rmip(self):
        return self._selected_solvers[gmoProc_rmip]
    def set_rmip(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_rmip):
            self._selected_solvers[gmoProc_rmip] = value
    ## @brief Default rmip solver
    rmip = property(get_rmip, set_rmip)

    def get_nlp(self):
        return self._selected_solvers[gmoProc_nlp]
    def set_nlp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_nlp):
            self._selected_solvers[gmoProc_nlp] = value
    ## @brief Default nlp solver
    nlp = property(get_nlp, set_nlp)

    def get_mcp(self):
        return self._selected_solvers[gmoProc_mcp]
    def set_mcp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_mcp):
            self._selected_solvers[gmoProc_mcp] = value
    ## @brief Default mcp solver
    mcp = property(get_mcp, set_mcp)

    def get_mpec(self):
        return self._selected_solvers[gmoProc_mpec]
    def set_mpec(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_mpec):
            self._selected_solvers[gmoProc_mpec] = value
    ## @brief Default mpec solver
    mpec = property(get_mpec, set_mpec)

    def get_rmpec(self):
        return self._selected_solvers[gmoProc_rmpec]
    def set_rmpec(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_rmpec):
            self._selected_solvers[gmoProc_rmpec] = value
    ## @brief Default rmpec solver
    rmpec = property(get_rmpec, set_rmpec)

    def get_cns(self):
        return self._selected_solvers[gmoProc_cns]
    def set_cns(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_cns):
            self._selected_solvers[gmoProc_cns] = value
    ## @brief Default cns solver
    cns = property(get_cns, set_cns)

    def get_dnlp(self):
        return self._selected_solvers[gmoProc_dnlp]
    def set_dnlp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_dnlp):
            self._selected_solvers[gmoProc_dnlp] = value
    ## @brief Default dnlp solver
    dnlp = property(get_dnlp, set_dnlp)

    def get_rminlp(self):
        return self._selected_solvers[gmoProc_rminlp]
    def set_rminlp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_rminlp):
            self._selected_solvers[gmoProc_rminlp] = value
    ## @brief Default rminlp solver
    rminlp = property(get_rminlp, set_rminlp)

    def get_minlp(self):
        return self._selected_solvers[gmoProc_minlp]
    def set_minlp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_minlp):
            self._selected_solvers[gmoProc_minlp] = value
    ## @brief Default minlp solver
    minlp = property(get_minlp, set_minlp)

    def get_qcp(self):
        return self._selected_solvers[gmoProc_qcp]
    def set_qcp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_qcp):
            self._selected_solvers[gmoProc_qcp] = value
    ## @brief Default qcp solver
    qcp = property(get_qcp, set_qcp)

    def get_miqcp(self):
        return self._selected_solvers[gmoProc_miqcp]
    def set_miqcp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_miqcp):
            self._selected_solvers[gmoProc_miqcp] = value
    ## @brief Default miqcp solver
    miqcp = property(get_miqcp, set_miqcp)

    def get_rmiqcp(self):
        return self._selected_solvers[gmoProc_rmiqcp]
    def set_rmiqcp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_rmiqcp):
            self._selected_solvers[gmoProc_rmiqcp] = value
    ## @brief Default rmiqcp solver
    rmiqcp = property(get_rmiqcp, set_rmiqcp)

    def get_emp(self):
        return self._selected_solvers[gmoProc_emp]
    def set_emp(self, value):
        if cfgAlgCapability(self._cfg, cfgAlgNumber(self._cfg, value), gmoProc_emp):
            self._selected_solvers[gmoProc_emp] = value
    ## @brief Default emp solver
    emp = property(get_emp, set_emp)

    def get_action(self):
        return optGetStrStr(self._opt, "Action")
    def set_action(self, value):
        optSetStrStr(self._opt, "Action", value)
    ## @brief GAMS processing request
    action = property(get_action, set_action)

    def get_appendexpand(self):
        return optGetIntStr(self._opt, "AppendExpand")
    def set_appendexpand(self, value):
        optSetIntStr(self._opt, "AppendExpand", value)
    ## @brief Expand file append option
    appendexpand = property(get_appendexpand, set_appendexpand)

    def _get_appendlog(self):
        return optGetIntStr(self._opt, "AppendLog")
    def _set_appendlog(self, value):
        optSetIntStr(self._opt, "AppendLog", value)
    _appendlog = property(_get_appendlog, _set_appendlog)

    def get_appendout(self):
        return optGetIntStr(self._opt, "AppendOut")
    def set_appendout(self, value):
        optSetIntStr(self._opt, "AppendOut", value)
    ## @brief Output file append option
    appendout = property(get_appendout, set_appendout)

    def get_asyncsollst(self):
        return optGetIntStr(self._opt, "AsyncSolLst")
    def set_asyncsollst(self, value):
        optSetIntStr(self._opt, "AsyncSolLst", value)
    ## @brief Print solution listing when asynchronous solve (Grid or Threads) is used
    asyncsollst = property(get_asyncsollst, set_asyncsollst)

    def get_bratio(self):
        return optGetDblStr(self._opt, "Bratio")
    def set_bratio(self, value):
        optSetDblStr(self._opt, "Bratio", value)
    ## @brief Basis detection threshold
    bratio = property(get_bratio, set_bratio)

    def get_capturemodelinstance(self):
        return optGetIntStr(self._opt, "CaptureModelInstance")
    def set_capturemodelinstance(self, value):
        optSetIntStr(self._opt, "CaptureModelInstance", value)
    ## @brief Switch to capture all model instances within a run
    capturemodelinstance = property(get_capturemodelinstance, set_capturemodelinstance)

    def get_case(self):
        return optGetIntStr(self._opt, "Case")
    def set_case(self, value):
        optSetIntStr(self._opt, "Case", value)
    ## @brief Output case option for LST file
    case = property(get_case, set_case)

    def get_cerr(self):
        return optGetIntStr(self._opt, "CErr")
    def set_cerr(self, value):
        optSetIntStr(self._opt, "CErr", value)
    ## @brief Compile time error limit
    cerr = property(get_cerr, set_cerr)

    def get_charset(self):
        return optGetIntStr(self._opt, "CharSet")
    def set_charset(self, value):
        optSetIntStr(self._opt, "CharSet", value)
    ## @brief Character set flag
    charset = property(get_charset, set_charset)

    def get_checkerrorlevel(self):
        return optGetIntStr(self._opt, "CheckErrorLevel")
    def set_checkerrorlevel(self, value):
        optSetIntStr(self._opt, "CheckErrorLevel", value)
    ## @brief Check errorLevel automatically after executing external program
    checkerrorlevel = property(get_checkerrorlevel, set_checkerrorlevel)

    def _get_compilerpreview(self):
        return optGetIntStr(self._opt, "CompilerPreview")
    def _set_compilerpreview(self, value):
        optSetIntStr(self._opt, "CompilerPreview", value)
    _compilerpreview = property(_get_compilerpreview, _set_compilerpreview)

    def _get_connectin(self):
        return optGetStrStr(self._opt, "ConnectIn")
    def _set_connectin(self, value):
        optSetStrStr(self._opt, "ConnectIn", value)
    _connectin = property(_get_connectin, _set_connectin)

    def _get_connectout(self):
        return optGetStrStr(self._opt, "ConnectOut")
    def _set_connectout(self, value):
        optSetStrStr(self._opt, "ConnectOut", value)
    _connectout = property(_get_connectout, _set_connectout)

    def _get_curdir(self):
        return optGetStrStr(self._opt, "CurDir")
    def _set_curdir(self, value):
        optSetStrStr(self._opt, "CurDir", value)
    _curdir = property(_get_curdir, _set_curdir)

    def _get_debugport(self):
        return optGetIntStr(self._opt, "DebugPort")
    def _set_debugport(self, value):
        optSetIntStr(self._opt, "DebugPort", value)
    _debugport = property(_get_debugport, _set_debugport)

    def get_decryptkey(self):
        return optGetStrStr(self._opt, "DecryptKey")
    def set_decryptkey(self, value):
        optSetStrStr(self._opt, "DecryptKey", value)
    ## @brief Key to decrypt a text file that was encrypted via $encrypt
    decryptkey = property(get_decryptkey, set_decryptkey)

    def get_dformat(self):
        return optGetIntStr(self._opt, "DFormat")
    def set_dformat(self, value):
        optSetIntStr(self._opt, "DFormat", value)
    ## @brief Date format
    dformat = property(get_dformat, set_dformat)

    def get_digit(self):
        return optGetStrStr(self._opt, "Digit")
    def set_digit(self, value):
        optSetStrStr(self._opt, "Digit", value)
    ## @brief Switch default for "$on/offDigit"
    digit = property(get_digit, set_digit)

    def _get_docfile(self):
        return optGetStrStr(self._opt, "DocFile")
    def _set_docfile(self, value):
        optSetStrStr(self._opt, "DocFile", value)
    _docfile = property(_get_docfile, _set_docfile)

    def get_domlim(self):
        return optGetIntStr(self._opt, "DomLim")
    def set_domlim(self, value):
        optSetIntStr(self._opt, "DomLim", value)
    ## @brief Domain violation limit solver default
    domlim = property(get_domlim, set_domlim)

    def get_dumpopt(self):
        return optGetIntStr(self._opt, "DumpOpt")
    def set_dumpopt(self, value):
        optSetIntStr(self._opt, "DumpOpt", value)
    ## @brief Writes preprocessed input to the file input.dmp
    dumpopt = property(get_dumpopt, set_dumpopt)

    def get_dumpoptgdx(self):
        return optGetStrStr(self._opt, "DumpOptGDX")
    def set_dumpoptgdx(self, value):
        optSetStrStr(self._opt, "DumpOptGDX", value)
    ## @brief Defines a GDX file name stem created when using DumpOpt
    dumpoptgdx = property(get_dumpoptgdx, set_dumpoptgdx)

    def get_dumpparms(self):
        return optGetIntStr(self._opt, "DumpParms")
    def set_dumpparms(self, value):
        optSetIntStr(self._opt, "DumpParms", value)
    ## @brief GAMS parameter logging
    dumpparms = property(get_dumpparms, set_dumpparms)

    def get_dumpparmslogprefix(self):
        return optGetStrStr(self._opt, "DumpParmsLogPrefix")
    def set_dumpparmslogprefix(self, value):
        optSetStrStr(self._opt, "DumpParmsLogPrefix", value)
    ## @brief Prefix of lines triggered by DumpParms>1
    dumpparmslogprefix = property(get_dumpparmslogprefix, set_dumpparmslogprefix)

    def get_ecimplicitload(self):
        return optGetStrStr(self._opt, "ECImplicitLoad")
    def set_ecimplicitload(self, value):
        optSetStrStr(self._opt, "ECImplicitLoad", value)
    ## @brief Allow implicit loading of symbols from embedded code or not
    ecimplicitload = property(get_ecimplicitload, set_ecimplicitload)

    def get_empty(self):
        return optGetStrStr(self._opt, "Empty")
    def set_empty(self, value):
        optSetStrStr(self._opt, "Empty", value)
    ## @brief Switch default for "$on/offEmpty"
    empty = property(get_empty, set_empty)

    def get_encryptkey(self):
        return optGetStrStr(self._opt, "EncryptKey")
    def set_encryptkey(self, value):
        optSetStrStr(self._opt, "EncryptKey", value)
    ## @brief Key to encrypt a text file using $encrypt
    encryptkey = property(get_encryptkey, set_encryptkey)

    def get_eolcom(self):
        return optGetStrStr(self._opt, "EolCom")
    def set_eolcom(self, value):
        optSetStrStr(self._opt, "EolCom", value)
    ## @brief Switch default for "$on/offEolCom" and "$eolCom"
    eolcom = property(get_eolcom, set_eolcom)

    def _get_epstozero(self):
        return optGetStrStr(self._opt, "EpsToZero")
    def _set_epstozero(self, value):
        optSetStrStr(self._opt, "EpsToZero", value)
    _epstozero = property(_get_epstozero, _set_epstozero)

    def get_errmsg(self):
        return optGetIntStr(self._opt, "ErrMsg")
    def set_errmsg(self, value):
        optSetIntStr(self._opt, "ErrMsg", value)
    ## @brief Placing of compilation error messages
    errmsg = property(get_errmsg, set_errmsg)

    def _get_errnam(self):
        return optGetStrStr(self._opt, "ErrNam")
    def _set_errnam(self, value):
        optSetStrStr(self._opt, "ErrNam", value)
    _errnam = property(_get_errnam, _set_errnam)

    def get_errorlog(self):
        return optGetIntStr(self._opt, "ErrorLog")
    def set_errorlog(self, value):
        optSetIntStr(self._opt, "ErrorLog", value)
    ## @brief Max error message lines written to the log for each error
    errorlog = property(get_errorlog, set_errorlog)

    def get_etlim(self):
        return optGetDblStr(self._opt, "ETLim")
    def set_etlim(self, value):
        optSetDblStr(self._opt, "ETLim", value)
    ## @brief Elapsed time limit in seconds
    etlim = property(get_etlim, set_etlim)

    def get_execmode(self):
        return optGetIntStr(self._opt, "ExecMode")
    def set_execmode(self, value):
        optSetIntStr(self._opt, "ExecMode", value)
    ## @brief Limits on external programs that are allowed to be executed
    execmode = property(get_execmode, set_execmode)

    def get_expand(self):
        return optGetStrStr(self._opt, "Expand")
    def set_expand(self, value):
        optSetStrStr(self._opt, "Expand", value)
    ## @brief Expanded (include) input file name
    expand = property(get_expand, set_expand)

    def get_fddelta(self):
        return optGetDblStr(self._opt, "FDDelta")
    def set_fddelta(self, value):
        optSetDblStr(self._opt, "FDDelta", value)
    ## @brief Step size for finite differences
    fddelta = property(get_fddelta, set_fddelta)

    def get_fdopt(self):
        return optGetIntStr(self._opt, "FDOpt")
    def set_fdopt(self, value):
        optSetIntStr(self._opt, "FDOpt", value)
    ## @brief Options for finite differences
    fdopt = property(get_fdopt, set_fdopt)

    def get_ferr(self):
        return optGetStrStr(self._opt, "FErr")
    def set_ferr(self, value):
        optSetStrStr(self._opt, "FErr", value)
    ## @brief Alternative error message file
    ferr = property(get_ferr, set_ferr)

    def get_filecase(self):
        return optGetIntStr(self._opt, "FileCase")
    def set_filecase(self, value):
        optSetIntStr(self._opt, "FileCase", value)
    ## @brief Casing of file names and paths (put, gdx, ref, $include, etc.)
    filecase = property(get_filecase, set_filecase)

    def get_filestem(self):
        return optGetStrStr(self._opt, "FileStem")
    def set_filestem(self, value):
        optSetStrStr(self._opt, "FileStem", value)
    ## @brief Sets the file stem for output files which use the input file name as stem by default
    filestem = property(get_filestem, set_filestem)

    def get_filestemapfromenv(self):
        return optGetStrStr(self._opt, "FileStemApFromEnv")
    def set_filestemapfromenv(self, value):
        optSetStrStr(self._opt, "FileStemApFromEnv", value)
    ## @brief Append a string read from an environment variable to the "FileStem"
    filestemapfromenv = property(get_filestemapfromenv, set_filestemapfromenv)

    def get_filtered(self):
        return optGetStrStr(self._opt, "Filtered")
    def set_filtered(self, value):
        optSetStrStr(self._opt, "Filtered", value)
    ## @brief Switch between filtered and domain-checked read from GDX
    filtered = property(get_filtered, set_filtered)

    def get_forceoptfile(self):
        return optGetIntStr(self._opt, "ForceOptFile")
    def set_forceoptfile(self, value):
        optSetIntStr(self._opt, "ForceOptFile", value)
    ## @brief Overwrites other option file section mechanism
    forceoptfile = property(get_forceoptfile, set_forceoptfile)

    def get_forcework(self):
        return optGetIntStr(self._opt, "ForceWork")
    def set_forcework(self, value):
        optSetIntStr(self._opt, "ForceWork", value)
    ## @brief Force GAMS to process a save file created with a newer GAMS version or with execution errors
    forcework = property(get_forcework, set_forcework)

    def get_forlim(self):
        return optGetIntStr(self._opt, "ForLim")
    def set_forlim(self, value):
        optSetIntStr(self._opt, "ForLim", value)
    ## @brief GAMS looping limit
    forlim = property(get_forlim, set_forlim)

    def get_freeembeddedpython(self):
        return optGetIntStr(self._opt, "FreeEmbeddedPython")
    def set_freeembeddedpython(self, value):
        optSetIntStr(self._opt, "FreeEmbeddedPython", value)
    ## @brief Free external resources at the end of each embedded Python code blocks
    freeembeddedpython = property(get_freeembeddedpython, set_freeembeddedpython)

    def _get_fsave(self):
        return optGetIntStr(self._opt, "FSave")
    def _set_fsave(self, value):
        optSetIntStr(self._opt, "FSave", value)
    _fsave = property(_get_fsave, _set_fsave)

    def _get_g205(self):
        return optGetIntStr(self._opt, "G205")
    def _set_g205(self, value):
        optSetIntStr(self._opt, "G205", value)
    _g205 = property(_get_g205, _set_g205)

    def get_gdxcompress(self):
        return optGetIntStr(self._opt, "gdxCompress")
    def set_gdxcompress(self, value):
        optSetIntStr(self._opt, "gdxCompress", value)
    ## @brief Compression of generated GDX file
    gdxcompress = property(get_gdxcompress, set_gdxcompress)

    def get_gdxconvert(self):
        return optGetStrStr(self._opt, "gdxConvert")
    def set_gdxconvert(self, value):
        optSetStrStr(self._opt, "gdxConvert", value)
    ## @brief Version of GDX files generated (for backward compatibility)
    gdxconvert = property(get_gdxconvert, set_gdxconvert)

    def _get_gdxsymbols(self):
        return optGetStrStr(self._opt, "gdxSymbols")
    def _set_gdxsymbols(self, value):
        optSetStrStr(self._opt, "gdxSymbols", value)
    _gdxsymbols = property(_get_gdxsymbols, _set_gdxsymbols)

    def get_gdxuels(self):
        return optGetStrStr(self._opt, "gdxUels")
    def set_gdxuels(self, value):
        optSetStrStr(self._opt, "gdxUels", value)
    ## @brief Unload labels or UELs to GDX either squeezed or full
    gdxuels = property(get_gdxuels, set_gdxuels)

    def _get_gp_solveline(self):
        return optGetStrStr(self._opt, "GP_SolveLine")
    def _set_gp_solveline(self, value):
        optSetStrStr(self._opt, "GP_SolveLine", value)
    _gp_solveline = property(_get_gp_solveline, _set_gp_solveline)

    def get_griddir(self):
        return optGetStrStr(self._opt, "GridDir")
    def set_griddir(self, value):
        optSetStrStr(self._opt, "GridDir", value)
    ## @brief Grid file directory
    griddir = property(get_griddir, set_griddir)

    def get_gridscript(self):
        return optGetStrStr(self._opt, "GridScript")
    def set_gridscript(self, value):
        optSetStrStr(self._opt, "GridScript", value)
    ## @brief Grid submission script
    gridscript = property(get_gridscript, set_gridscript)

    def get_heaplimit(self):
        return optGetDblStr(self._opt, "HeapLimit")
    def set_heaplimit(self, value):
        optSetDblStr(self._opt, "HeapLimit", value)
    ## @brief Maximum Heap size allowed in MB
    heaplimit = property(get_heaplimit, set_heaplimit)

    def get_holdfixed(self):
        return optGetIntStr(self._opt, "HoldFixed")
    def set_holdfixed(self, value):
        optSetIntStr(self._opt, "HoldFixed", value)
    ## @brief Treat fixed variables as constants
    holdfixed = property(get_holdfixed, set_holdfixed)

    def get_holdfixedasync(self):
        return optGetIntStr(self._opt, "HoldFixedAsync")
    def set_holdfixedasync(self, value):
        optSetIntStr(self._opt, "HoldFixedAsync", value)
    ## @brief Allow HoldFixed for models solved asynchronously as well
    holdfixedasync = property(get_holdfixedasync, set_holdfixedasync)

    def get_idcgdxinput(self):
        return optGetStrStr(self._opt, "IDCGDXInput")
    def set_idcgdxinput(self, value):
        optSetStrStr(self._opt, "IDCGDXInput", value)
    ## @brief GDX file name with data for implicit input
    idcgdxinput = property(get_idcgdxinput, set_idcgdxinput)

    def get_idcgdxoutput(self):
        return optGetStrStr(self._opt, "IDCGDXOutput")
    def set_idcgdxoutput(self, value):
        optSetStrStr(self._opt, "IDCGDXOutput", value)
    ## @brief GDX file name for data for implicit output
    idcgdxoutput = property(get_idcgdxoutput, set_idcgdxoutput)

    def _get_idcgenerategdx(self):
        return optGetStrStr(self._opt, "IDCGenerateGDX")
    def _set_idcgenerategdx(self, value):
        optSetStrStr(self._opt, "IDCGenerateGDX", value)
    _idcgenerategdx = property(_get_idcgenerategdx, _set_idcgenerategdx)

    def _get_idcgenerategdxinput(self):
        return optGetStrStr(self._opt, "IDCGenerateGDXInput")
    def _set_idcgenerategdxinput(self, value):
        optSetStrStr(self._opt, "IDCGenerateGDXInput", value)
    _idcgenerategdxinput = property(_get_idcgenerategdxinput, _set_idcgenerategdxinput)

    def _get_idcgenerategdxoutput(self):
        return optGetStrStr(self._opt, "IDCGenerateGDXOutput")
    def _set_idcgenerategdxoutput(self, value):
        optSetStrStr(self._opt, "IDCGenerateGDXOutput", value)
    _idcgenerategdxoutput = property(_get_idcgenerategdxoutput, _set_idcgenerategdxoutput)

    def _get_idcgeneratejson(self):
        return optGetStrStr(self._opt, "IDCGenerateJSON")
    def _set_idcgeneratejson(self, value):
        optSetStrStr(self._opt, "IDCGenerateJSON", value)
    _idcgeneratejson = property(_get_idcgeneratejson, _set_idcgeneratejson)

    def _get_idcjson(self):
        return optGetStrStr(self._opt, "IDCJSON")
    def _set_idcjson(self, value):
        optSetStrStr(self._opt, "IDCJSON", value)
    _idcjson = property(_get_idcjson, _set_idcjson)

    def _get_idcprotect(self):
        return optGetIntStr(self._opt, "IDCProtect")
    def _set_idcprotect(self, value):
        optSetIntStr(self._opt, "IDCProtect", value)
    _idcprotect = property(_get_idcprotect, _set_idcprotect)

    def _get_ide(self):
        return optGetIntStr(self._opt, "IDE")
    def _set_ide(self, value):
        optSetIntStr(self._opt, "IDE", value)
    _ide = property(_get_ide, _set_ide)

    def get_implicitassign(self):
        return optGetStrStr(self._opt, "ImplicitAssign")
    def set_implicitassign(self, value):
        optSetStrStr(self._opt, "ImplicitAssign", value)
    ## @brief Switch default for "$on/offImplicitAssign"
    implicitassign = property(get_implicitassign, set_implicitassign)

    def _get_incrementalmode(self):
        return optGetIntStr(self._opt, "IncrementalMode")
    def _set_incrementalmode(self, value):
        optSetIntStr(self._opt, "IncrementalMode", value)
    _incrementalmode = property(_get_incrementalmode, _set_incrementalmode)

    def get_inlinecom(self):
        return optGetStrStr(self._opt, "InlineCom")
    def set_inlinecom(self, value):
        optSetStrStr(self._opt, "InlineCom", value)
    ## @brief Switch default for "$on/offInline" and "$inlineCom"
    inlinecom = property(get_inlinecom, set_inlinecom)

    def _get_input(self):
        return optGetStrStr(self._opt, "Input")
    def _set_input(self, value):
        optSetStrStr(self._opt, "Input", value)
    _input = property(_get_input, _set_input)

    def _get_inputdir(self):
        return optGetStrStr(self._opt, "InputDir")
    def _set_inputdir(self, value):
        optSetStrStr(self._opt, "InputDir", value)
    _inputdir = property(_get_inputdir, _set_inputdir)

    def _get_inputdir1(self):
        return optGetStrStr(self._opt, "InputDir1")
    def _set_inputdir1(self, value):
        optSetStrStr(self._opt, "InputDir1", value)
    _inputdir1 = property(_get_inputdir1, _set_inputdir1)

    def _get_inputdir2(self):
        return optGetStrStr(self._opt, "InputDir2")
    def _set_inputdir2(self, value):
        optSetStrStr(self._opt, "InputDir2", value)
    _inputdir2 = property(_get_inputdir2, _set_inputdir2)

    def _get_inputdir3(self):
        return optGetStrStr(self._opt, "InputDir3")
    def _set_inputdir3(self, value):
        optSetStrStr(self._opt, "InputDir3", value)
    _inputdir3 = property(_get_inputdir3, _set_inputdir3)

    def _get_inputdir4(self):
        return optGetStrStr(self._opt, "InputDir4")
    def _set_inputdir4(self, value):
        optSetStrStr(self._opt, "InputDir4", value)
    _inputdir4 = property(_get_inputdir4, _set_inputdir4)

    def _get_inputdir5(self):
        return optGetStrStr(self._opt, "InputDir5")
    def _set_inputdir5(self, value):
        optSetStrStr(self._opt, "InputDir5", value)
    _inputdir5 = property(_get_inputdir5, _set_inputdir5)

    def _get_inputdir6(self):
        return optGetStrStr(self._opt, "InputDir6")
    def _set_inputdir6(self, value):
        optSetStrStr(self._opt, "InputDir6", value)
    _inputdir6 = property(_get_inputdir6, _set_inputdir6)

    def _get_inputdir7(self):
        return optGetStrStr(self._opt, "InputDir7")
    def _set_inputdir7(self, value):
        optSetStrStr(self._opt, "InputDir7", value)
    _inputdir7 = property(_get_inputdir7, _set_inputdir7)

    def _get_inputdir8(self):
        return optGetStrStr(self._opt, "InputDir8")
    def _set_inputdir8(self, value):
        optSetStrStr(self._opt, "InputDir8", value)
    _inputdir8 = property(_get_inputdir8, _set_inputdir8)

    def _get_inputdir9(self):
        return optGetStrStr(self._opt, "InputDir9")
    def _set_inputdir9(self, value):
        optSetStrStr(self._opt, "InputDir9", value)
    _inputdir9 = property(_get_inputdir9, _set_inputdir9)

    def _get_inputdir10(self):
        return optGetStrStr(self._opt, "InputDir10")
    def _set_inputdir10(self, value):
        optSetStrStr(self._opt, "InputDir10", value)
    _inputdir10 = property(_get_inputdir10, _set_inputdir10)

    def _get_inputdir11(self):
        return optGetStrStr(self._opt, "InputDir11")
    def _set_inputdir11(self, value):
        optSetStrStr(self._opt, "InputDir11", value)
    _inputdir11 = property(_get_inputdir11, _set_inputdir11)

    def _get_inputdir12(self):
        return optGetStrStr(self._opt, "InputDir12")
    def _set_inputdir12(self, value):
        optSetStrStr(self._opt, "InputDir12", value)
    _inputdir12 = property(_get_inputdir12, _set_inputdir12)

    def _get_inputdir13(self):
        return optGetStrStr(self._opt, "InputDir13")
    def _set_inputdir13(self, value):
        optSetStrStr(self._opt, "InputDir13", value)
    _inputdir13 = property(_get_inputdir13, _set_inputdir13)

    def _get_inputdir14(self):
        return optGetStrStr(self._opt, "InputDir14")
    def _set_inputdir14(self, value):
        optSetStrStr(self._opt, "InputDir14", value)
    _inputdir14 = property(_get_inputdir14, _set_inputdir14)

    def _get_inputdir15(self):
        return optGetStrStr(self._opt, "InputDir15")
    def _set_inputdir15(self, value):
        optSetStrStr(self._opt, "InputDir15", value)
    _inputdir15 = property(_get_inputdir15, _set_inputdir15)

    def _get_inputdir16(self):
        return optGetStrStr(self._opt, "InputDir16")
    def _set_inputdir16(self, value):
        optSetStrStr(self._opt, "InputDir16", value)
    _inputdir16 = property(_get_inputdir16, _set_inputdir16)

    def _get_inputdir17(self):
        return optGetStrStr(self._opt, "InputDir17")
    def _set_inputdir17(self, value):
        optSetStrStr(self._opt, "InputDir17", value)
    _inputdir17 = property(_get_inputdir17, _set_inputdir17)

    def _get_inputdir18(self):
        return optGetStrStr(self._opt, "InputDir18")
    def _set_inputdir18(self, value):
        optSetStrStr(self._opt, "InputDir18", value)
    _inputdir18 = property(_get_inputdir18, _set_inputdir18)

    def _get_inputdir19(self):
        return optGetStrStr(self._opt, "InputDir19")
    def _set_inputdir19(self, value):
        optSetStrStr(self._opt, "InputDir19", value)
    _inputdir19 = property(_get_inputdir19, _set_inputdir19)

    def _get_inputdir20(self):
        return optGetStrStr(self._opt, "InputDir20")
    def _set_inputdir20(self, value):
        optSetStrStr(self._opt, "InputDir20", value)
    _inputdir20 = property(_get_inputdir20, _set_inputdir20)

    def _get_inputdir21(self):
        return optGetStrStr(self._opt, "InputDir21")
    def _set_inputdir21(self, value):
        optSetStrStr(self._opt, "InputDir21", value)
    _inputdir21 = property(_get_inputdir21, _set_inputdir21)

    def _get_inputdir22(self):
        return optGetStrStr(self._opt, "InputDir22")
    def _set_inputdir22(self, value):
        optSetStrStr(self._opt, "InputDir22", value)
    _inputdir22 = property(_get_inputdir22, _set_inputdir22)

    def _get_inputdir23(self):
        return optGetStrStr(self._opt, "InputDir23")
    def _set_inputdir23(self, value):
        optSetStrStr(self._opt, "InputDir23", value)
    _inputdir23 = property(_get_inputdir23, _set_inputdir23)

    def _get_inputdir24(self):
        return optGetStrStr(self._opt, "InputDir24")
    def _set_inputdir24(self, value):
        optSetStrStr(self._opt, "InputDir24", value)
    _inputdir24 = property(_get_inputdir24, _set_inputdir24)

    def _get_inputdir25(self):
        return optGetStrStr(self._opt, "InputDir25")
    def _set_inputdir25(self, value):
        optSetStrStr(self._opt, "InputDir25", value)
    _inputdir25 = property(_get_inputdir25, _set_inputdir25)

    def _get_inputdir26(self):
        return optGetStrStr(self._opt, "InputDir26")
    def _set_inputdir26(self, value):
        optSetStrStr(self._opt, "InputDir26", value)
    _inputdir26 = property(_get_inputdir26, _set_inputdir26)

    def _get_inputdir27(self):
        return optGetStrStr(self._opt, "InputDir27")
    def _set_inputdir27(self, value):
        optSetStrStr(self._opt, "InputDir27", value)
    _inputdir27 = property(_get_inputdir27, _set_inputdir27)

    def _get_inputdir28(self):
        return optGetStrStr(self._opt, "InputDir28")
    def _set_inputdir28(self, value):
        optSetStrStr(self._opt, "InputDir28", value)
    _inputdir28 = property(_get_inputdir28, _set_inputdir28)

    def _get_inputdir29(self):
        return optGetStrStr(self._opt, "InputDir29")
    def _set_inputdir29(self, value):
        optSetStrStr(self._opt, "InputDir29", value)
    _inputdir29 = property(_get_inputdir29, _set_inputdir29)

    def _get_inputdir30(self):
        return optGetStrStr(self._opt, "InputDir30")
    def _set_inputdir30(self, value):
        optSetStrStr(self._opt, "InputDir30", value)
    _inputdir30 = property(_get_inputdir30, _set_inputdir30)

    def _get_inputdir31(self):
        return optGetStrStr(self._opt, "InputDir31")
    def _set_inputdir31(self, value):
        optSetStrStr(self._opt, "InputDir31", value)
    _inputdir31 = property(_get_inputdir31, _set_inputdir31)

    def _get_inputdir32(self):
        return optGetStrStr(self._opt, "InputDir32")
    def _set_inputdir32(self, value):
        optSetStrStr(self._opt, "InputDir32", value)
    _inputdir32 = property(_get_inputdir32, _set_inputdir32)

    def _get_inputdir33(self):
        return optGetStrStr(self._opt, "InputDir33")
    def _set_inputdir33(self, value):
        optSetStrStr(self._opt, "InputDir33", value)
    _inputdir33 = property(_get_inputdir33, _set_inputdir33)

    def _get_inputdir34(self):
        return optGetStrStr(self._opt, "InputDir34")
    def _set_inputdir34(self, value):
        optSetStrStr(self._opt, "InputDir34", value)
    _inputdir34 = property(_get_inputdir34, _set_inputdir34)

    def _get_inputdir35(self):
        return optGetStrStr(self._opt, "InputDir35")
    def _set_inputdir35(self, value):
        optSetStrStr(self._opt, "InputDir35", value)
    _inputdir35 = property(_get_inputdir35, _set_inputdir35)

    def _get_inputdir36(self):
        return optGetStrStr(self._opt, "InputDir36")
    def _set_inputdir36(self, value):
        optSetStrStr(self._opt, "InputDir36", value)
    _inputdir36 = property(_get_inputdir36, _set_inputdir36)

    def _get_inputdir37(self):
        return optGetStrStr(self._opt, "InputDir37")
    def _set_inputdir37(self, value):
        optSetStrStr(self._opt, "InputDir37", value)
    _inputdir37 = property(_get_inputdir37, _set_inputdir37)

    def _get_inputdir38(self):
        return optGetStrStr(self._opt, "InputDir38")
    def _set_inputdir38(self, value):
        optSetStrStr(self._opt, "InputDir38", value)
    _inputdir38 = property(_get_inputdir38, _set_inputdir38)

    def _get_inputdir39(self):
        return optGetStrStr(self._opt, "InputDir39")
    def _set_inputdir39(self, value):
        optSetStrStr(self._opt, "InputDir39", value)
    _inputdir39 = property(_get_inputdir39, _set_inputdir39)

    def _get_inputdir40(self):
        return optGetStrStr(self._opt, "InputDir40")
    def _set_inputdir40(self, value):
        optSetStrStr(self._opt, "InputDir40", value)
    _inputdir40 = property(_get_inputdir40, _set_inputdir40)

    def get_integer1(self):
        return optGetIntStr(self._opt, "Integer1")
    def set_integer1(self, value):
        optSetIntStr(self._opt, "Integer1", value)
    ## @brief Integer communication cell N
    integer1 = property(get_integer1, set_integer1)

    def get_integer2(self):
        return optGetIntStr(self._opt, "Integer2")
    def set_integer2(self, value):
        optSetIntStr(self._opt, "Integer2", value)
    ## @brief Integer communication cell N
    integer2 = property(get_integer2, set_integer2)

    def get_integer3(self):
        return optGetIntStr(self._opt, "Integer3")
    def set_integer3(self, value):
        optSetIntStr(self._opt, "Integer3", value)
    ## @brief Integer communication cell N
    integer3 = property(get_integer3, set_integer3)

    def get_integer4(self):
        return optGetIntStr(self._opt, "Integer4")
    def set_integer4(self, value):
        optSetIntStr(self._opt, "Integer4", value)
    ## @brief Integer communication cell N
    integer4 = property(get_integer4, set_integer4)

    def get_integer5(self):
        return optGetIntStr(self._opt, "Integer5")
    def set_integer5(self, value):
        optSetIntStr(self._opt, "Integer5", value)
    ## @brief Integer communication cell N
    integer5 = property(get_integer5, set_integer5)

    def get_interactivesolver(self):
        return optGetIntStr(self._opt, "InteractiveSolver")
    def set_interactivesolver(self, value):
        optSetIntStr(self._opt, "InteractiveSolver", value)
    ## @brief Allow solver to interact via command line input
    interactivesolver = property(get_interactivesolver, set_interactivesolver)

    def get_intvarup(self):
        return optGetIntStr(self._opt, "IntVarUp")
    def set_intvarup(self, value):
        optSetIntStr(self._opt, "IntVarUp", value)
    ## @brief Set mode for default upper bounds on integer variables
    intvarup = property(get_intvarup, set_intvarup)

    def get_iterlim(self):
        return optGetIntStr(self._opt, "IterLim")
    def set_iterlim(self, value):
        optSetIntStr(self._opt, "IterLim", value)
    ## @brief Iteration limit of solver
    iterlim = property(get_iterlim, set_iterlim)

    def get_jobtrace(self):
        return optGetStrStr(self._opt, "JobTrace")
    def set_jobtrace(self, value):
        optSetStrStr(self._opt, "JobTrace", value)
    ## @brief Job trace string to be written to the trace file at the end of a GAMS job
    jobtrace = property(get_jobtrace, set_jobtrace)

    def get_keep(self):
        return optGetIntStr(self._opt, "Keep")
    def set_keep(self, value):
        optSetIntStr(self._opt, "Keep", value)
    ## @brief Controls keeping or deletion of process directory and scratch files
    keep = property(get_keep, set_keep)

    def get_libincdir(self):
        return optGetStrStr(self._opt, "LibIncDir")
    def set_libincdir(self, value):
        optSetStrStr(self._opt, "LibIncDir", value)
    ## @brief LibInclude directory
    libincdir = property(get_libincdir, set_libincdir)

    def get_license(self):
        return optGetStrStr(self._opt, "License")
    def set_license(self, value):
        optSetStrStr(self._opt, "License", value)
    ## @brief Use alternative license file
    license = property(get_license, set_license)

    def get_limcol(self):
        return optGetIntStr(self._opt, "LimCol")
    def set_limcol(self, value):
        optSetIntStr(self._opt, "LimCol", value)
    ## @brief Maximum number of columns listed in one variable block
    limcol = property(get_limcol, set_limcol)

    def get_limrow(self):
        return optGetIntStr(self._opt, "LimRow")
    def set_limrow(self, value):
        optSetIntStr(self._opt, "LimRow", value)
    ## @brief Maximum number of rows listed in one equation block
    limrow = property(get_limrow, set_limrow)

    def get_listing(self):
        return optGetStrStr(self._opt, "Listing")
    def set_listing(self, value):
        optSetStrStr(self._opt, "Listing", value)
    ## @brief Switch default for "$on/offListing"
    listing = property(get_listing, set_listing)

    def _get_logfile(self):
        return optGetStrStr(self._opt, "LogFile")
    def _set_logfile(self, value):
        optSetStrStr(self._opt, "LogFile", value)
    _logfile = property(_get_logfile, _set_logfile)

    def get_logline(self):
        return optGetIntStr(self._opt, "LogLine")
    def set_logline(self, value):
        optSetIntStr(self._opt, "LogLine", value)
    ## @brief Amount of line tracing to the log file
    logline = property(get_logline, set_logline)

    def _get_logoption(self):
        return optGetIntStr(self._opt, "LogOption")
    def _set_logoption(self, value):
        optSetIntStr(self._opt, "LogOption", value)
    _logoption = property(_get_logoption, _set_logoption)

    def get_lsttitleleftaligned(self):
        return optGetIntStr(self._opt, "LstTitleLeftAligned")
    def set_lsttitleleftaligned(self, value):
        optSetIntStr(self._opt, "LstTitleLeftAligned", value)
    ## @brief Write title of LST file all left aligned
    lsttitleleftaligned = property(get_lsttitleleftaligned, set_lsttitleleftaligned)

    def get_maxexecerror(self):
        return optGetIntStr(self._opt, "MaxExecError")
    def set_maxexecerror(self, value):
        optSetIntStr(self._opt, "MaxExecError", value)
    ## @brief Execution time error limit
    maxexecerror = property(get_maxexecerror, set_maxexecerror)

    def _get_maxgenericfiles(self):
        return optGetIntStr(self._opt, "MaxGenericFiles")
    def _set_maxgenericfiles(self, value):
        optSetIntStr(self._opt, "MaxGenericFiles", value)
    _maxgenericfiles = property(_get_maxgenericfiles, _set_maxgenericfiles)

    def get_maxprocdir(self):
        return optGetIntStr(self._opt, "MaxProcDir")
    def set_maxprocdir(self, value):
        optSetIntStr(self._opt, "MaxProcDir", value)
    ## @brief Maximum number of 225* process directories
    maxprocdir = property(get_maxprocdir, set_maxprocdir)

    def _get_mcprholdfx(self):
        return optGetIntStr(self._opt, "MCPRHoldfx")
    def _set_mcprholdfx(self, value):
        optSetIntStr(self._opt, "MCPRHoldfx", value)
    _mcprholdfx = property(_get_mcprholdfx, _set_mcprholdfx)

    def get_miimode(self):
        return optGetStrStr(self._opt, "MIIMode")
    def set_miimode(self, value):
        optSetStrStr(self._opt, "MIIMode", value)
    ## @brief Model Instance Mode
    miimode = property(get_miimode, set_miimode)

    def get_multi(self):
        return optGetStrStr(self._opt, "Multi")
    def set_multi(self, value):
        optSetStrStr(self._opt, "Multi", value)
    ## @brief Switch default for "$on/offMulti[R]"
    multi = property(get_multi, set_multi)

    def _get_multipass(self):
        return optGetIntStr(self._opt, "MultiPass")
    def _set_multipass(self, value):
        optSetIntStr(self._opt, "MultiPass", value)
    _multipass = property(_get_multipass, _set_multipass)

    def _get_netlicense(self):
        return optGetStrStr(self._opt, "NetLicense")
    def _set_netlicense(self, value):
        optSetStrStr(self._opt, "NetLicense", value)
    _netlicense = property(_get_netlicense, _set_netlicense)

    def _get_nocr(self):
        return optGetIntStr(self._opt, "NoCr")
    def _set_nocr(self, value):
        optSetIntStr(self._opt, "NoCr", value)
    _nocr = property(_get_nocr, _set_nocr)

    def get_nodlim(self):
        return optGetIntStr(self._opt, "NodLim")
    def set_nodlim(self, value):
        optSetIntStr(self._opt, "NodLim", value)
    ## @brief Node limit in branch and bound tree
    nodlim = property(get_nodlim, set_nodlim)

    def get_nonewvarequ(self):
        return optGetIntStr(self._opt, "NoNewVarEqu")
    def set_nonewvarequ(self, value):
        optSetIntStr(self._opt, "NoNewVarEqu", value)
    ## @brief Triggers a compilation error when new equations or variable symbols are introduced
    nonewvarequ = property(get_nonewvarequ, set_nonewvarequ)

    def get_on115(self):
        return optGetIntStr(self._opt, "On115")
    def set_on115(self, value):
        optSetIntStr(self._opt, "On115", value)
    ## @brief Generate errors for unknown unique element in an equation
    on115 = property(get_on115, set_on115)

    def get_optca(self):
        return optGetDblStr(self._opt, "OptCA")
    def set_optca(self, value):
        optSetDblStr(self._opt, "OptCA", value)
    ## @brief Absolute Optimality criterion solver default
    optca = property(get_optca, set_optca)

    def get_optcr(self):
        return optGetDblStr(self._opt, "OptCR")
    def set_optcr(self, value):
        optSetDblStr(self._opt, "OptCR", value)
    ## @brief Relative Optimality criterion solver default
    optcr = property(get_optcr, set_optcr)

    def get_optdir(self):
        return optGetStrStr(self._opt, "OptDir")
    def set_optdir(self, value):
        optSetStrStr(self._opt, "OptDir", value)
    ## @brief Option file directory
    optdir = property(get_optdir, set_optdir)

    def get_optfile(self):
        return optGetIntStr(self._opt, "OptFile")
    def set_optfile(self, value):
        optSetIntStr(self._opt, "OptFile", value)
    ## @brief Default option file
    optfile = property(get_optfile, set_optfile)

    def get_output(self):
        return optGetStrStr(self._opt, "Output")
    def set_output(self, value):
        optSetStrStr(self._opt, "Output", value)
    ## @brief Listing file name
    output = property(get_output, set_output)

    def get_pagecontr(self):
        return optGetIntStr(self._opt, "PageContr")
    def set_pagecontr(self, value):
        optSetIntStr(self._opt, "PageContr", value)
    ## @brief Output file page control option
    pagecontr = property(get_pagecontr, set_pagecontr)

    def get_pagesize(self):
        return optGetIntStr(self._opt, "PageSize")
    def set_pagesize(self, value):
        optSetIntStr(self._opt, "PageSize", value)
    ## @brief Output file page size (=0 no paging)
    pagesize = property(get_pagesize, set_pagesize)

    def get_pagewidth(self):
        return optGetIntStr(self._opt, "PageWidth")
    def set_pagewidth(self, value):
        optSetIntStr(self._opt, "PageWidth", value)
    ## @brief Output file page width
    pagewidth = property(get_pagewidth, set_pagewidth)

    def _get_pid2error(self):
        return optGetIntStr(self._opt, "PID2Error")
    def _set_pid2error(self, value):
        optSetIntStr(self._opt, "PID2Error", value)
    _pid2error = property(_get_pid2error, _set_pid2error)

    def get_plicense(self):
        return optGetStrStr(self._opt, "PLicense")
    def set_plicense(self, value):
        optSetStrStr(self._opt, "PLicense", value)
    ## @brief Privacy license file name
    plicense = property(get_plicense, set_plicense)

    def get_prefixloadpath(self):
        return optGetIntStr(self._opt, "PrefixLoadPath")
    def set_prefixloadpath(self, value):
        optSetIntStr(self._opt, "PrefixLoadPath", value)
    ## @brief Prepend GAMS system directory to library load path
    prefixloadpath = property(get_prefixloadpath, set_prefixloadpath)

    def get_previouswork(self):
        return optGetIntStr(self._opt, "PreviousWork")
    def set_previouswork(self, value):
        optSetIntStr(self._opt, "PreviousWork", value)
    ## @brief Indicator for writing workfile with previous workfile version
    previouswork = property(get_previouswork, set_previouswork)

    def _get_procdir(self):
        return optGetStrStr(self._opt, "ProcDir")
    def _set_procdir(self, value):
        optSetStrStr(self._opt, "ProcDir", value)
    _procdir = property(_get_procdir, _set_procdir)

    def _get_procdirpath(self):
        return optGetStrStr(self._opt, "ProcDirPath")
    def _set_procdirpath(self, value):
        optSetStrStr(self._opt, "ProcDirPath", value)
    _procdirpath = property(_get_procdirpath, _set_procdirpath)

    def get_proctreememmonitor(self):
        return optGetIntStr(self._opt, "ProcTreeMemMonitor")
    def set_proctreememmonitor(self, value):
        optSetIntStr(self._opt, "ProcTreeMemMonitor", value)
    ## @brief Monitor the memory used by the GAMS process tree
    proctreememmonitor = property(get_proctreememmonitor, set_proctreememmonitor)

    def get_proctreememticks(self):
        return optGetIntStr(self._opt, "ProcTreeMemTicks")
    def set_proctreememticks(self, value):
        optSetIntStr(self._opt, "ProcTreeMemTicks", value)
    ## @brief Set wait interval between memory monitor checks: ticks = milliseconds
    proctreememticks = property(get_proctreememticks, set_proctreememticks)

    def get_profile(self):
        return optGetIntStr(self._opt, "Profile")
    def set_profile(self, value):
        optSetIntStr(self._opt, "Profile", value)
    ## @brief Execution profiling
    profile = property(get_profile, set_profile)

    def get_profilefile(self):
        return optGetStrStr(self._opt, "ProfileFile")
    def set_profilefile(self, value):
        optSetStrStr(self._opt, "ProfileFile", value)
    ## @brief Write profile information to this file
    profilefile = property(get_profilefile, set_profilefile)

    def get_profiletol(self):
        return optGetDblStr(self._opt, "ProfileTol")
    def set_profiletol(self, value):
        optSetDblStr(self._opt, "ProfileTol", value)
    ## @brief Minimum time a statement must use to appear in profile generated output
    profiletol = property(get_profiletol, set_profiletol)

    def get_putdir(self):
        return optGetStrStr(self._opt, "PutDir")
    def set_putdir(self, value):
        optSetStrStr(self._opt, "PutDir", value)
    ## @brief Put file directory
    putdir = property(get_putdir, set_putdir)

    def get_putnd(self):
        return optGetIntStr(self._opt, "PutND")
    def set_putnd(self, value):
        optSetIntStr(self._opt, "PutND", value)
    ## @brief Number of decimals for put files
    putnd = property(get_putnd, set_putnd)

    def get_putnr(self):
        return optGetIntStr(self._opt, "PutNR")
    def set_putnr(self, value):
        optSetIntStr(self._opt, "PutNR", value)
    ## @brief Numeric round format for put files
    putnr = property(get_putnr, set_putnr)

    def get_putps(self):
        return optGetIntStr(self._opt, "PutPS")
    def set_putps(self, value):
        optSetIntStr(self._opt, "PutPS", value)
    ## @brief Page size for put files
    putps = property(get_putps, set_putps)

    def get_putpw(self):
        return optGetIntStr(self._opt, "PutPW")
    def set_putpw(self, value):
        optSetIntStr(self._opt, "PutPW", value)
    ## @brief Page width for put files
    putpw = property(get_putpw, set_putpw)

    def get_reference(self):
        return optGetStrStr(self._opt, "Reference")
    def set_reference(self, value):
        optSetStrStr(self._opt, "Reference", value)
    ## @brief Symbol reference file
    reference = property(get_reference, set_reference)

    def get_referencelineno(self):
        return optGetStrStr(self._opt, "ReferenceLineNo")
    def set_referencelineno(self, value):
        optSetStrStr(self._opt, "ReferenceLineNo", value)
    ## @brief Controls the line numbers written to a reference file
    referencelineno = property(get_referencelineno, set_referencelineno)

    def _get_relpath(self):
        return optGetIntStr(self._opt, "RelPath")
    def _set_relpath(self, value):
        optSetIntStr(self._opt, "RelPath", value)
    _relpath = property(_get_relpath, _set_relpath)

    def get_replace(self):
        return optGetStrStr(self._opt, "Replace")
    def set_replace(self, value):
        optSetStrStr(self._opt, "Replace", value)
    ## @brief Switch between merge and replace when reading from GDX into non-empty symbol
    replace = property(get_replace, set_replace)

    def get_reslim(self):
        return optGetDblStr(self._opt, "ResLim")
    def set_reslim(self, value):
        optSetDblStr(self._opt, "ResLim", value)
    ## @brief Wall-clock time limit for solver
    reslim = property(get_reslim, set_reslim)

    def _get_restart(self):
        return optGetStrStr(self._opt, "Restart")
    def _set_restart(self, value):
        optSetStrStr(self._opt, "Restart", value)
    _restart = property(_get_restart, _set_restart)

    def _get_restartnamed(self):
        return optGetStrStr(self._opt, "RestartNamed")
    def _set_restartnamed(self, value):
        optSetStrStr(self._opt, "RestartNamed", value)
    _restartnamed = property(_get_restartnamed, _set_restartnamed)

    def _get_save(self):
        return optGetStrStr(self._opt, "Save")
    def _set_save(self, value):
        optSetStrStr(self._opt, "Save", value)
    _save = property(_get_save, _set_save)

    def _get_saveobfuscate(self):
        return optGetStrStr(self._opt, "SaveObfuscate")
    def _set_saveobfuscate(self, value):
        optSetStrStr(self._opt, "SaveObfuscate", value)
    _saveobfuscate = property(_get_saveobfuscate, _set_saveobfuscate)

    def get_savepoint(self):
        return optGetIntStr(self._opt, "SavePoint")
    def set_savepoint(self, value):
        optSetIntStr(self._opt, "SavePoint", value)
    ## @brief Save solver point in GDX file
    savepoint = property(get_savepoint, set_savepoint)

    def _get_scrdir(self):
        return optGetStrStr(self._opt, "ScrDir")
    def _set_scrdir(self, value):
        optSetStrStr(self._opt, "ScrDir", value)
    _scrdir = property(_get_scrdir, _set_scrdir)

    def _get_scrext(self):
        return optGetStrStr(self._opt, "ScrExt")
    def _set_scrext(self, value):
        optSetStrStr(self._opt, "ScrExt", value)
    _scrext = property(_get_scrext, _set_scrext)

    def get_scriptexit(self):
        return optGetStrStr(self._opt, "ScriptExit")
    def set_scriptexit(self, value):
        optSetStrStr(self._opt, "ScriptExit", value)
    ## @brief Program or script to be executed at the end of a GAMS run
    scriptexit = property(get_scriptexit, set_scriptexit)

    def _get_scriptfrst(self):
        return optGetStrStr(self._opt, "ScriptFrst")
    def _set_scriptfrst(self, value):
        optSetStrStr(self._opt, "ScriptFrst", value)
    _scriptfrst = property(_get_scriptfrst, _set_scriptfrst)

    def _get_scriptnext(self):
        return optGetStrStr(self._opt, "ScriptNext")
    def _set_scriptnext(self, value):
        optSetStrStr(self._opt, "ScriptNext", value)
    _scriptnext = property(_get_scriptnext, _set_scriptnext)

    def _get_scrnam(self):
        return optGetStrStr(self._opt, "ScrNam")
    def _set_scrnam(self, value):
        optSetStrStr(self._opt, "ScrNam", value)
    _scrnam = property(_get_scrnam, _set_scrnam)

    def get_seed(self):
        return optGetIntStr(self._opt, "Seed")
    def set_seed(self, value):
        optSetIntStr(self._opt, "Seed", value)
    ## @brief Random number seed
    seed = property(get_seed, set_seed)

    def _get_serverrun(self):
        return optGetIntStr(self._opt, "ServerRun")
    def _set_serverrun(self, value):
        optSetIntStr(self._opt, "ServerRun", value)
    _serverrun = property(_get_serverrun, _set_serverrun)

    def get_showosmemory(self):
        return optGetIntStr(self._opt, "ShowOSMemory")
    def set_showosmemory(self, value):
        optSetIntStr(self._opt, "ShowOSMemory", value)
    ## @brief Show the memory usage reported by the Operating System instead of the internal counting
    showosmemory = property(get_showosmemory, set_showosmemory)

    def get_solprint(self):
        return optGetIntStr(self._opt, "SolPrint")
    def set_solprint(self, value):
        optSetIntStr(self._opt, "SolPrint", value)
    ## @brief Solution report print option
    solprint = property(get_solprint, set_solprint)

    def get_solvelink(self):
        return optGetIntStr(self._opt, "SolveLink")
    def set_solvelink(self, value):
        optSetIntStr(self._opt, "SolveLink", value)
    ## @brief Solver link option
    solvelink = property(get_solvelink, set_solvelink)

    def get_solveopt(self):
        return optGetIntStr(self._opt, "SolveOpt")
    def set_solveopt(self, value):
        optSetIntStr(self._opt, "SolveOpt", value)
    ## @brief Multiple solve management
    solveopt = property(get_solveopt, set_solveopt)

    def _get_solver(self):
        return optGetStrStr(self._opt, "Solver")
    def _set_solver(self, value):
        optSetStrStr(self._opt, "Solver", value)
    _solver = property(_get_solver, _set_solver)

    def _get_solvercntr(self):
        return optGetStrStr(self._opt, "SolverCntr")
    def _set_solvercntr(self, value):
        optSetStrStr(self._opt, "SolverCntr", value)
    _solvercntr = property(_get_solvercntr, _set_solvercntr)

    def _get_solverdict(self):
        return optGetStrStr(self._opt, "SolverDict")
    def _set_solverdict(self, value):
        optSetStrStr(self._opt, "SolverDict", value)
    _solverdict = property(_get_solverdict, _set_solverdict)

    def _get_solverinst(self):
        return optGetStrStr(self._opt, "SolverInst")
    def _set_solverinst(self, value):
        optSetStrStr(self._opt, "SolverInst", value)
    _solverinst = property(_get_solverinst, _set_solverinst)

    def _get_solvermatr(self):
        return optGetStrStr(self._opt, "SolverMatr")
    def _set_solvermatr(self, value):
        optSetStrStr(self._opt, "SolverMatr", value)
    _solvermatr = property(_get_solvermatr, _set_solvermatr)

    def _get_solversolu(self):
        return optGetStrStr(self._opt, "SolverSolu")
    def _set_solversolu(self, value):
        optSetStrStr(self._opt, "SolverSolu", value)
    _solversolu = property(_get_solversolu, _set_solversolu)

    def _get_solverstat(self):
        return optGetStrStr(self._opt, "SolverStat")
    def _set_solverstat(self, value):
        optSetStrStr(self._opt, "SolverStat", value)
    _solverstat = property(_get_solverstat, _set_solverstat)

    def _get_sparserun(self):
        return optGetStrStr(self._opt, "SparseRun")
    def _set_sparserun(self, value):
        optSetStrStr(self._opt, "SparseRun", value)
    _sparserun = property(_get_sparserun, _set_sparserun)

    def _get_sqacmex(self):
        return optGetStrStr(self._opt, "SqaCmex")
    def _set_sqacmex(self, value):
        optSetStrStr(self._opt, "SqaCmex", value)
    _sqacmex = property(_get_sqacmex, _set_sqacmex)

    def get_stepsum(self):
        return optGetIntStr(self._opt, "StepSum")
    def set_stepsum(self, value):
        optSetIntStr(self._opt, "StepSum", value)
    ## @brief Summary of computing resources used by job steps
    stepsum = property(get_stepsum, set_stepsum)

    def get_strictsingleton(self):
        return optGetIntStr(self._opt, "strictSingleton")
    def set_strictsingleton(self, value):
        optSetIntStr(self._opt, "strictSingleton", value)
    ## @brief Error if assignment to singleton set has multiple elements
    strictsingleton = property(get_strictsingleton, set_strictsingleton)

    def get_stringchk(self):
        return optGetIntStr(self._opt, "StringChk")
    def set_stringchk(self, value):
        optSetIntStr(self._opt, "StringChk", value)
    ## @brief String substitution options
    stringchk = property(get_stringchk, set_stringchk)

    def _get_subsys(self):
        return optGetStrStr(self._opt, "SubSys")
    def _set_subsys(self, value):
        optSetStrStr(self._opt, "SubSys", value)
    _subsys = property(_get_subsys, _set_subsys)

    def get_suffixdlvars(self):
        return optGetStrStr(self._opt, "SuffixDLVars")
    def set_suffixdlvars(self, value):
        optSetStrStr(self._opt, "SuffixDLVars", value)
    ## @brief Switch default for "$on/offSuffixDLVars"
    suffixdlvars = property(get_suffixdlvars, set_suffixdlvars)

    def get_suffixalgebravars(self):
        return optGetStrStr(self._opt, "SuffixAlgebraVars")
    def set_suffixalgebravars(self, value):
        optSetStrStr(self._opt, "SuffixAlgebraVars", value)
    ## @brief Switch default for "$on/offSuffixAlgebraVars"
    suffixalgebravars = property(get_suffixalgebravars, set_suffixalgebravars)

    def get_suppress(self):
        return optGetIntStr(self._opt, "Suppress")
    def set_suppress(self, value):
        optSetIntStr(self._opt, "Suppress", value)
    ## @brief Compiler listing option
    suppress = property(get_suppress, set_suppress)

    def get_symbol(self):
        return optGetStrStr(self._opt, "Symbol")
    def set_symbol(self, value):
        optSetStrStr(self._opt, "Symbol", value)
    ## @brief Symbol table file
    symbol = property(get_symbol, set_symbol)

    def get_symprefix(self):
        return optGetStrStr(self._opt, "SymPrefix")
    def set_symprefix(self, value):
        optSetStrStr(self._opt, "SymPrefix", value)
    ## @brief Prefix all symbols encountered during compilation by the specified string in work file
    symprefix = property(get_symprefix, set_symprefix)

    def get_sys10(self):
        return optGetIntStr(self._opt, "Sys10")
    def set_sys10(self, value):
        optSetIntStr(self._opt, "Sys10", value)
    ## @brief Changes rpower to ipower when the exponent is constant and within 1e-12 of an integer
    sys10 = property(get_sys10, set_sys10)

    def get_sys11(self):
        return optGetIntStr(self._opt, "Sys11")
    def set_sys11(self, value):
        optSetIntStr(self._opt, "Sys11", value)
    ## @brief Dynamic resorting if indices in assignment/data statements are not in natural order
    sys11 = property(get_sys11, set_sys11)

    def get_sys12(self):
        return optGetIntStr(self._opt, "Sys12")
    def set_sys12(self, value):
        optSetIntStr(self._opt, "Sys12", value)
    ## @brief Pass model with generation errors to solver
    sys12 = property(get_sys12, set_sys12)

    def _get_sys14(self):
        return optGetIntStr(self._opt, "Sys14")
    def _set_sys14(self, value):
        optSetIntStr(self._opt, "Sys14", value)
    _sys14 = property(_get_sys14, _set_sys14)

    def _get_sys15(self):
        return optGetIntStr(self._opt, "Sys15")
    def _set_sys15(self, value):
        optSetIntStr(self._opt, "Sys15", value)
    _sys15 = property(_get_sys15, _set_sys15)

    def _get_sys16(self):
        return optGetIntStr(self._opt, "Sys16")
    def _set_sys16(self, value):
        optSetIntStr(self._opt, "Sys16", value)
    _sys16 = property(_get_sys16, _set_sys16)

    def _get_sys17(self):
        return optGetIntStr(self._opt, "Sys17")
    def _set_sys17(self, value):
        optSetIntStr(self._opt, "Sys17", value)
    _sys17 = property(_get_sys17, _set_sys17)

    def _get_sys18(self):
        return optGetIntStr(self._opt, "Sys18")
    def _set_sys18(self, value):
        optSetIntStr(self._opt, "Sys18", value)
    _sys18 = property(_get_sys18, _set_sys18)

    def _get_sys19(self):
        return optGetIntStr(self._opt, "Sys19")
    def _set_sys19(self, value):
        optSetIntStr(self._opt, "Sys19", value)
    _sys19 = property(_get_sys19, _set_sys19)

    def _get_sysdir(self):
        return optGetStrStr(self._opt, "SysDir")
    def _set_sysdir(self, value):
        optSetStrStr(self._opt, "SysDir", value)
    _sysdir = property(_get_sysdir, _set_sysdir)

    def get_sysincdir(self):
        return optGetStrStr(self._opt, "SysIncDir")
    def set_sysincdir(self, value):
        optSetStrStr(self._opt, "SysIncDir", value)
    ## @brief SysInclude directory
    sysincdir = property(get_sysincdir, set_sysincdir)

    def get_sysout(self):
        return optGetIntStr(self._opt, "SysOut")
    def set_sysout(self, value):
        optSetIntStr(self._opt, "SysOut", value)
    ## @brief Solver Status file reporting option
    sysout = property(get_sysout, set_sysout)

    def get_tabin(self):
        return optGetIntStr(self._opt, "TabIn")
    def set_tabin(self, value):
        optSetIntStr(self._opt, "TabIn", value)
    ## @brief Tab spacing
    tabin = property(get_tabin, set_tabin)

    def get_tformat(self):
        return optGetIntStr(self._opt, "TFormat")
    def set_tformat(self, value):
        optSetIntStr(self._opt, "TFormat", value)
    ## @brief Time format
    tformat = property(get_tformat, set_tformat)

    def get_threads(self):
        return optGetIntStr(self._opt, "Threads")
    def set_threads(self, value):
        optSetIntStr(self._opt, "Threads", value)
    ## @brief Number of processors to be used by a solver
    threads = property(get_threads, set_threads)

    def get_threadsasync(self):
        return optGetIntStr(self._opt, "ThreadsAsync")
    def set_threadsasync(self, value):
        optSetIntStr(self._opt, "ThreadsAsync", value)
    ## @brief Limit on number of threads to be used for asynchronous solves (solveLink=6)
    threadsasync = property(get_threadsasync, set_threadsasync)

    def get_timer(self):
        return optGetIntStr(self._opt, "Timer")
    def set_timer(self, value):
        optSetIntStr(self._opt, "Timer", value)
    ## @brief Instruction timer threshold in milli seconds
    timer = property(get_timer, set_timer)

    def get_trace(self):
        return optGetStrStr(self._opt, "Trace")
    def set_trace(self, value):
        optSetStrStr(self._opt, "Trace", value)
    ## @brief Trace file name
    trace = property(get_trace, set_trace)

    def get_tracelevel(self):
        return optGetIntStr(self._opt, "TraceLevel")
    def set_tracelevel(self, value):
        optSetIntStr(self._opt, "TraceLevel", value)
    ## @brief Modelstat/Solvestat threshold used in conjunction with action=GT
    tracelevel = property(get_tracelevel, set_tracelevel)

    def get_traceopt(self):
        return optGetIntStr(self._opt, "TraceOpt")
    def set_traceopt(self, value):
        optSetIntStr(self._opt, "TraceOpt", value)
    ## @brief Trace file format option
    traceopt = property(get_traceopt, set_traceopt)

    def get_user1(self):
        return optGetStrStr(self._opt, "User1")
    def set_user1(self, value):
        optSetStrStr(self._opt, "User1", value)
    ## @brief User string N
    user1 = property(get_user1, set_user1)

    def get_user2(self):
        return optGetStrStr(self._opt, "User2")
    def set_user2(self, value):
        optSetStrStr(self._opt, "User2", value)
    ## @brief User string N
    user2 = property(get_user2, set_user2)

    def get_user3(self):
        return optGetStrStr(self._opt, "User3")
    def set_user3(self, value):
        optSetStrStr(self._opt, "User3", value)
    ## @brief User string N
    user3 = property(get_user3, set_user3)

    def get_user4(self):
        return optGetStrStr(self._opt, "User4")
    def set_user4(self, value):
        optSetStrStr(self._opt, "User4", value)
    ## @brief User string N
    user4 = property(get_user4, set_user4)

    def get_user5(self):
        return optGetStrStr(self._opt, "User5")
    def set_user5(self, value):
        optSetStrStr(self._opt, "User5", value)
    ## @brief User string N
    user5 = property(get_user5, set_user5)

    def get_warnings(self):
        return optGetIntStr(self._opt, "Warnings")
    def set_warnings(self, value):
        optSetIntStr(self._opt, "Warnings", value)
    ## @brief Number of warnings permitted before a run terminates
    warnings = property(get_warnings, set_warnings)

    def _get_workdir(self):
        return optGetStrStr(self._opt, "WorkDir")
    def _set_workdir(self, value):
        optSetStrStr(self._opt, "WorkDir", value)
    _workdir = property(_get_workdir, _set_workdir)

    def get_workfactor(self):
        return optGetDblStr(self._opt, "WorkFactor")
    def set_workfactor(self, value):
        optSetDblStr(self._opt, "WorkFactor", value)
    ## @brief Memory Estimate multiplier for some solvers
    workfactor = property(get_workfactor, set_workfactor)

    def get_workspace(self):
        return optGetDblStr(self._opt, "WorkSpace")
    def set_workspace(self, value):
        optSetDblStr(self._opt, "WorkSpace", value)
    ## @brief Work space for some solvers in MB
    workspace = property(get_workspace, set_workspace)

    def _get_writeoutput(self):
        return optGetIntStr(self._opt, "writeOutput")
    def _set_writeoutput(self, value):
        optSetIntStr(self._opt, "writeOutput", value)
    _writeoutput = property(_get_writeoutput, _set_writeoutput)

    def _get_xsave(self):
        return optGetStrStr(self._opt, "XSave")
    def _set_xsave(self, value):
        optSetStrStr(self._opt, "XSave", value)
    _xsave = property(_get_xsave, _set_xsave)

    def _get_xsaveobfuscate(self):
        return optGetStrStr(self._opt, "XSaveObfuscate")
    def _set_xsaveobfuscate(self, value):
        optSetStrStr(self._opt, "XSaveObfuscate", value)
    _xsaveobfuscate = property(_get_xsaveobfuscate, _set_xsaveobfuscate)

    def get_zerores(self):
        return optGetDblStr(self._opt, "ZeroRes")
    def set_zerores(self, value):
        optSetDblStr(self._opt, "ZeroRes", value)
    ## @brief The results of certain operations will be set to zero if abs(result) LE ZeroRes
    zerores = property(get_zerores, set_zerores)

    def get_zeroresrep(self):
        return optGetIntStr(self._opt, "ZeroResRep")
    def set_zeroresrep(self, value):
        optSetIntStr(self._opt, "ZeroResRep", value)
    ## @brief Report underflow as a warning when abs(results) LE ZeroRes and result set to zero
    zeroresrep = property(get_zeroresrep, set_zeroresrep)

    def _get_gdx(self):
        return optGetStrStr(self._opt, "GDX")
    def _set_gdx(self, value):
        optSetStrStr(self._opt, "GDX", os.path.splitext(value)[0] + ".gdx")
    gdx = property(_get_gdx, _set_gdx)

    _api_ver = "48.4.0"

    def __init__(self, ws, opt_from=None, opt_file=None):
        '''
        @brief Constructor
        @param ws GamsWorkspace containing GamsOptions
        @param opt_from GamsOptions used to initialize the new object
        @param opt_file Parameter used to initialize the new objectfile
        '''

        ws._debug_out("---- Entering GamsOptions constructor ----", 0)

        ## @brief GAMS Dash Options
        self.defines = {}
        self._selected_solvers = []
        self.idir = []
        self._opt = new_optHandle_tp()
        self._cfg = new_cfgHandle_tp()

        self._workspace = ws

        ret = optCreateD(self._opt, self._workspace._system_directory, GMS_SSSIZE)
        if not ret[0]:
            raise gams.control.workspace.GamsException(ret[1])
        def_file = self._workspace._system_directory + os.sep + "optgams.def"
        GamsOptions.optLock.acquire()
        rc = optReadDefinition(self._opt, def_file)
        GamsOptions.optLock.release()
        if rc:
            for i in range(1, optMessageCount(self._opt)):
                ret = optGetMessage(self._opt, i)
            raise gams.control.workspace.GamsException("Problem reading definition file " + def_file)

        ret = cfgCreateD(self._cfg, self._workspace._system_directory, GMS_SSSIZE)
        if not ret[0]:
            raise gams.control.workspace.GamsException(ret[1])
        if gams.control.workspace._is_win:
            conf_file = "gmscmpnt.txt"
        else:
            conf_file = "gmscmpun.txt"

        if cfgReadConfigGUC(self._cfg, self._workspace._system_directory + os.sep + conf_file, self._workspace._system_directory):
            raise gams.control.workspace.GamsException("Error reading config file" + self._workspace._system_directory + os.sep + conf_file)

        if opt_from:
            #TODO: mktemp is depricated, but mkstemp created a file and we don't want that
            pf_file_name = tempfile.mktemp(prefix=self._workspace.scratch_file_prefix, dir=self._workspace._working_directory)
            optWriteParameterFile(opt_from._opt, pf_file_name)
            optReadParameterFile(self._opt, pf_file_name)

            #Copy special options
            for s in opt_from.idir:
                self.idir.append(s)
            for s in opt_from._selected_solvers:
                self._selected_solvers.append(s)
            for k, v in iter(opt_from.defines.items()):
                self.defines[k] = v

            if self._workspace._debug < gams.control.workspace.DebugLevel.KeepFiles:
                try:
                    os.remove(pf_file_name)
                except:
                    pass

        elif opt_file:
            if not os.path.isabs(opt_file):
                opt_file = os.path.join(self._workspace._working_directory, opt_file)
            if 0 != optReadParameterFile(self._opt, opt_file):
                msg_list = []
                for i in range(1, optMessageCount(self._opt) + 1):
                    msg_list.append(optGetMessage(self._opt, i)[0])
                msg = "\n".join(msg_list)
                raise gams.control.workspace.GamsException(f"Problem reading parameter file {opt_file}:\n{msg}")


            for i in range(1,41):
                if optGetDefinedStr(self._opt, "InputDir" + str(i)):
                    self.idir.append(optGetStrStr(self._opt, "InputDir" + str(i)))

            key = ""
            val = ""
            ret = optGetFromAnyStrList(self._opt, 1)
            while 0 != ret[0]:
                key = ret[1]
                val = ret[2]
                if key.startswith("--"):
                    key = key[2:]
                    self.defines[key] = val
                ret = optGetFromAnyStrList(self._opt, 1)

            # No clue what to do about SolverOptions

            self._selected_solvers.append("") # gmoProc_none
            for i in range(1, gmoProc_nrofmodeltypes):
                self._selected_solvers.append(cfgAlgName(self._cfg, cfgDefaultAlg(self._cfg, i)))

            for i in range(1, gmoProc_nrofmodeltypes):
                if (optGetDefinedStr(self._opt, cfgModelTypeName(self._cfg, i))):
                    self._selected_solvers[i] = optGetStrStr(self._opt, cfgModelTypeName(self._cfg,i))

        else:
            self._selected_solvers.append("") # gmoProc_none
            for i in range(1, gmoProc_nrofmodeltypes):
                self._selected_solvers.append(cfgAlgName(self._cfg, cfgDefaultAlg(self._cfg, i)))

    def export(self, file_path):
        '''
        @brief Write GamsOptions into a parameter file
        @param file_path The path used to write the parameter file. A relative path is relative to the GAMS working directory.
        '''

        if os.path.isabs(file_path):
            optWriteParameterFile(self._opt, file_path)
        else:
            file_path = os.path.join(self._workspace._working_directory, file_path)
            optWriteParameterFile(self._opt, file_path)
        file = open(file_path, "a")
        file.write("EolOnly=1" + "\n")
        if len(self.idir) > 0:
            if len(self.idir) > 40:
                    raise gams.control.workspace.GamsException("Cannot handle more than 40 IDirs")
            for i in range(1, len(self.idir)):
                file.write("InputDir" + str(i) + "=" + self.idir[i-1] + "\n")

        # SolverOptions ???
        for i in range(1, gmoProc_nrofmodeltypes):
            file.write(cfgModelTypeName(self._cfg, i) + "=" + self._selected_solvers[i] + "\n")
        if len(self.defines) > 0:
            for k,v in self.defines:
                file.write("--" + k + "=" + v + "\n")
        file.close()

    def __del__(self):
        self._workspace._debug_out("---- Entering GamsOptions destructor ----", 0)
        if self._opt != None:
            optFree(self._opt)
        if self._cfg != None:
            cfgFree(self._cfg)

