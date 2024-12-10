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

import filecmp
import tempfile
import os
import shutil
from subprocess import Popen
import threading
from warnings import warn
from gams.control.database import *
from gams.control.execution import *
from gams.control.options import *

import sys
_is_win = _is_linux = _is_osx = False
if sys.platform == "win32":
    _is_win =True
elif sys.platform.startswith("linux"):
    _is_linux = True
elif sys.platform == "darwin":
    _is_osx = True
else:
    raise Exception("Unknown operating system")


## @brief Exception class thrown for GAMS exceptions
class GamsException(Exception):
    def __init__(self, value, workspace=None):
        Exception.__init__(self, value)
        self.value = value
        if workspace is not None:
            workspace._has_error = True
    def __str__(self):
        return self.value

## @brief Exception class thrown for GAMS execution exceptions
class GamsExceptionExecution(GamsException):
    def __init__(self, value, exit_code, workspace=None):
        self.value = value
        self._rc = exit_code
        if workspace is not None:
            workspace._has_error = True
    ## brief GAMS return code
    def get_rc(self):
        return self._rc
    rc = property(get_rc)

    def __str__(self):
        return self.value


## @brief GAMS exit code
class GamsExitCode(object):
    ## @brief Normal Return
    NormalReturn = 0
    ## @brief Solver is to be called, the system should never return this number
    SolverToBeCalled = 1
    ## @brief There was a compilation error
    CompilationError = 2
    ## @brief There was an execution error
    ExecutionError = 3
    ## @brief System limits were reached
    SystemLimitsReached = 4
    ## @brief There was a file error
    FileError = 5
    ## @brief There was a parameter error
    ParameterError = 6
    ## @brief There was a licensing error
    LicensingError = 7
    ## @brief There was a GAMS system error
    GAMSSystemError = 8
    ## @brief GAMS cold not be started
    GAMSCouldNotBeStarted = 9
    ## @brief Out of memory
    OutOfMemory = 10
    ## @brief Out of of disk
    OutOfDisk = 11
    ## @brief Could not create process/scratch directory
    CouldNotCreateScratchDir = 109
    ## @brief Too many process/scratch directorie
    TooManyScratchDirs = 110
    ## @brief Could not delete the process/scratch directory
    CouldNotDeleteScratchDir = 112
    ## @brief Could not write "gamsnext" script
    CouldNotWriteGamsNext = 113
    ## @brief Could not write "parameter" file
    CouldNotWriteParamFile = 114
    ## @brief Could not read environment variable
    CouldNotReadEnvVar = 115
    ## @brief Could not spawn the GAMS language compiler (gamscmex)
    CouldNotSpawnGAMScmex = 400
    ## @brief Current directory (curdir) does not exist
    CurDirNotFound = 401
    ## @brief Cannot set current directory (curdir)
    CurDirNotSet = 402
    ## @brief Blank in system directory (UNIX only)
    BlankInSysDir = 404
    ## @brief Blank in current directory (UNIX only)
    BlankInCurDir = 405
    ## @brief Blank in scratch extension (scrext)
    BlankInScrExt = 406
    ## @brief Unexpected cmexRC
    UnexpectedCmexRC = 407
    ## @brief Could not find the process directory (procdir)
    ProcDirNotFound = 408
    ## @brief CMEX library not found (experimental)
    CmexLibNotFound = 409
    ## @brief Entry point in CMEX library not found (experimental)
    CmexLibEPNotFound = 410
    ## @brief Cannot add path / Unknown UNIX environment / Cannot set environment variable
    CannotAddPath = 909
    ## @brief Driver error: Missing command line parameter for gams.exe
    MissingCommandLineParameter = 1000
    ## @brief Driver error: Internal error: Cannot install interrupt handler
    CannotInstallInterrupt = 2000
    ## @brief Driver error: Problems getting current directory (sometimes caused by specifying the current directory in Microsoft UNC format)
    CouldNotGetCurrentDir = 3000
    ## @brief Driver error: Internal error: GAMS compile and execute module not found
    CmexNotFound = 4000
    ## @brief Driver error: Internal error: Cannot load option handling library
    OptNotFound = 5000


#TODO: move this to __init__.py to be loaded with the module
## @brief Equation subtype
class EquType(object):
    ## @brief Equality - =E=
    E = 0
    ## @brief Greater or equal than inequality - =G=
    G = 1
    ## @brief Less or equal than inequality - =L=
    L = 2
    ## @brief Non-binding equation - =N=
    N = 3
    ## @brief External equation - =X=
    X = 4
    ## @brief Cone equation - =C=
    C = 5


#TODO: move this to __init__.py to be loaded with the module
## @brief Variable subtype
class VarType(object):
    ## @brief Unknown variable type
    Unknown = 0
    ## @brief Binary variable
    Binary = 1
    ## @brief Integer Variable
    Integer = 2
    ## @brief Positive variable
    Positive = 3
    ## @brief Negative variable
    Negative = 4
    ## @brief Free variable
    Free = 5
    ## @brief Special Ordered Set 1
    SOS1 = 6
    ## @brief Special Ordered Set 2
    SOS2 = 7
    ## @brief Semi-continuous variable
    SemiCont = 8
    ## @brief Semi-integer variable
    SemiInt = 9


## @brief Set subtype
class SetType(object):
    ## @brief Multi Set - The Default
    Multi = 0
    ## @brief Singleton Set - Zero or one element
    Singleton = 1


#TODO: move this to __init__.py to be loaded with the module
## @brief Solver termination condition
class SolveStat(object):
    ## @brief Normal termination
    Normal = 1
    ## @brief Solver ran out of iterations
    Iteration = 2
    ## @brief Solver exceeded time limit
    Resource = 3
    ## @brief Solver quit with a problem
    Solver = 4
    ## @brief Solver quit with nonlinear term evaluation errors
    EvalError = 5
    ## @brief Solver terminated because the model is beyond the solvers capabilities
    Capability = 6
    ## @brief Solver terminated with a license error
    License = 7
    ## @brief Solver terminated on users request (e.g. Ctrl-C)
    User = 8
    ## @brief Solver terminated on setup error
    SetupErr = 9
    ## @brief Solver terminated with error
    SolverErr = 10
    ## @brief Solver terminated with error
    InternalErr = 11
    ## @brief Solve skipped
    Skipped = 12
    ## @brief Other error
    SystemErr = 13


#TODO: move this to __init__.py to be loaded with the module
## @brief Model Solution Status
class ModelStat(object):
    ## @brief Optimal solution achieved
    OptimalGlobal = 1
    ## @brief Local optimal solution achieved
    OptimalLocal = 2
    ## @brief Unbounded model found
    Unbounded = 3
    ## @brief Infeasible model found
    InfeasibleGlobal = 4
    ## @brief Locally infeasible model found
    InfeasibleLocal = 5
    ## @brief Solver terminated early and model was still infeasible
    InfeasibleIntermed = 6
    ## @brief Solver terminated early and model was feasible but not yet optimal
    Feasible = 7
    ## @brief Integer solution found
    Integer = 8
    ## @brief Solver terminated early with a non integer solution found
    NonIntegerIntermed = 9
    ## @brief No feasible integer solution could be found
    IntegerInfeasible = 10
    ## @brief Licensing problem
    LicenseError = 11
    ## @brief Error - No cause known
    ErrorUnknown = 12
    ## @brief Error - No solution attained
    ErrorNoSolution = 13
    ## @brief No solution returned
    NoSolutionReturned = 14
    ## @brief Unique solution in a CNS models
    SolvedUnique = 15
    ## @brief Feasible solution in a CNS models
    Solved = 16
    ## @brief Singular in a CNS models
    SolvedSingular = 17
    ## @brief Unbounded - no solution
    UnboundedNoSolution = 18
    ## @brief Infeasible - no solution
    InfeasibleNoSolution = 19

## @brief GAMS Debug Level
class DebugLevel(object):
    ## @brief No debug
    Off = 0
    ## @brief Keep temporary files only if GamsException/GamsExceptionExecution was raised in GamsJob.run(), GamsJob.run_engine(), or GamsModelInstance.solve()
    KeepFilesOnError = 1
    ## @brief Keep temporary files
    KeepFiles = 2
    ## @brief Send GAMS log to stdout and keep temporary files
    ShowLog = 3
    ## @brief Send highly technical info and GAMS log to stdout and keep temporary files
    Verbose = 4

class GamsWorkspace(object):
    '''
    @brief The GamsWorkspace is the base class of the gams.control API.
    @details  <p>Most objects of the
              control API (e.g. GamsDatabase and GamsJob) should be created by an "add"
              method of GamsWorkspace instead of using the constructors. </p>
              <p>Unless a GAMS system directory is specified during construction of
              GamsWorkspace, GamsWorkspace determines the location of the GAMS installation
              automatically. This is a source of potential  problems if more than one GAMS
              installation exist on the machine. </p>
              <p>Furthermore, a working directory (the anchor into the file system) can be
              provided when constructing the GamsWorkspace instance. All file based
              operation inside a GAMS model should be relative to this location (e.g. $GDXIN
              and $include). There are options to add input search paths (e.g. IDir) and
              output path (e.g. PutDir) to specify other file system locations. If no working
              directory is supplied, GamsWorkspace creates a temporary folder and on
              instance destruction removes this temporary folder. </p>
              <p>In a typical Python application a single instance of GamsWorkspace will
              suffice, since the class is thread-safe. </p>
              <h5>Working with different GAMS Versions on one Machine</h5>
              <p>When creating a new instance of GamsWorkspace, one way of defining the GAMS system
              directory is setting the system_directory parameter of the constructor accordingly. If it
              is not set, it is tried to be defined automatically (see \ref API_PY_CONTROL for details). However, this can be tricky if there
              is more than one version of GAMS installed on a machine and especially if there are
              different applications running with different GAMS versions.</p>
              <p>On Windows, the automatic identification relies on information left in the Windows registry by the
              GAMS installer. Hence the system directory of the last GAMS installation will be found in
              this automatic identification step. One way of resetting the information in the registry
              is running the executable "findthisgams.exe" from the directory that should be detected
              automatically. While this can be done from the outside of the application it is not much
              more convenient than the system_directory argument in the GamsWorkspace constructor.</p>
              <p>If one has a very structured way of organizing the GAMS installations (e.g. following
              the GAMS default installation location) one can use GamsWorkspace.api_version to point to
              the best matching GAMS system directory:</p>
              @code{.py}
              sysdir = "C:\\GAMS\\" + GamsWorkspace.api_version[:2]
              ws = GamsWorkspace(system_directory=sysdir)
              @endcode
              <p>This avoids the automatic identification of the GAMS system directory but might be the
              most convenient solution for systems running multiple applications using different versions
              of the GAMS Python API together with different versions of GAMS.</p>
    '''

    def set_eps(self,value):
        self._eps = value
    ## @brief Reset value to be stored in and read from GamsDatabase for Epsilon
    def get_eps(self):
        return self._eps
    ## @brief Get value to be stored in and read from GamsDatabase for Epsilon
    my_eps = property(get_eps, set_eps)

    def get_working_directory(self):
        return self._working_directory
    ## @brief GAMS working directory, anchor for all file-based operations
    working_directory = property(get_working_directory)


    def get_system_directory(self):
        return self._system_directory
    ## @brief GAMS system directory
    system_directory = property(get_system_directory)

    def get_version(self):
        return self._version
    ## @brief GAMS Version used
    version = property(get_version)

    def get_major_rel_number(self):
        return self._major_rel_number
    ## @brief GAMS Major Release Number
    major_rel_number = property(get_major_rel_number)

    def get_minor_rel_number(self):
        return self._minor_rel_number
    ## @brief GAMS Minor Release Number
    minor_rel_number = property(get_minor_rel_number)

    def get_gold_rel_number(self):
        return self._gold_rel_number
    ## @brief GAMS GOLD Release Number
    gold_rel_number = property(get_gold_rel_number)

    ## @brief GAMS API version
    api_version = GamsOptions._api_ver

    ## @brief GAMS API Major Release Number
    api_major_rel_number = int(GamsOptions._api_ver.split(".")[0])

    ## @brief GAMS API Minor Release Number
    api_minor_rel_number = int(GamsOptions._api_ver.split(".")[1])

    ## @brief GAMS API GOLD Release Number
    api_gold_rel_number  = int(GamsOptions._api_ver.split(".")[2])

    @staticmethod
    def _find_gams_win():
        gams_dir = ""
        if sys.version_info[0] >=3:
            import winreg as wreg
        else:
            import _winreg as wreg

        try:
            gams_dir = wreg.QueryValue(wreg.HKEY_CURRENT_USER, r"Software\Classes\gams.location")
        except:
            try:
                gams_dir = wreg.QueryValue(wreg.HKEY_LOCAL_MACHINE, r"Software\Classes\gams.location")
            except:
                pass
        return gams_dir

    @staticmethod
    def _find_ld_library_path(ld_string):
        gams_dir = ""
        try:
            if ld_string in os.environ:
                paths = os.environ[ld_string].split(":")
                for p in paths:
                    if os.path.exists(os.path.join(p, "gamsstmp.txt")):
                        gams_dir = p
                        break
        except:
            pass
        return gams_dir

    @staticmethod
    def is_same_system_directory(first, second):
        if os.path.exists(os.path.join(first, "gamsstmp.txt")) and os.path.exists(os.path.join(second, "gamsstmp.txt")):
            if filecmp.cmp( os.path.join(first, "gamsstmp.txt"), os.path.join(second, "gamsstmp.txt")):
                return True
            else:
                return False
        else:
            return False

    def _run_gams_audit(self):
        if _is_win:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            try:
                self._p = subprocess.Popen(self._system_directory + os.sep + "gams.exe audit lo=3", stdout=subprocess.PIPE, cwd=self._working_directory, startupinfo=si, creationflags=subprocess.CREATE_NEW_CONSOLE)
            except:
                raise GamsException("Error retrieving audit info")
        else:
            try:
                self._p = subprocess.Popen([self._system_directory + os.sep + "gams", "audit", "lo=3"], stdout=subprocess.PIPE, cwd=self._working_directory)
            except:
                raise GamsException("Error retrieving audit info")

        version_string = ""
        new_data = ""
        while True:
            # we don't want to get an exception when interrupting with ctrl-c
            try:
                new_data = self._p.stdout.readline()
                if sys.version_info[0] >=3:
                    new_data = new_data.decode()
                version_string += new_data
            except KeyboardInterrupt: pass
            if new_data == '' and self._p.poll() != None:
                break
        exitcode = self._p.wait()
        if exitcode != 0:
            raise GamsException("Error retrieving audit info")
        self._p.stdout.close()
        self._p = None
        return version_string

    def _parse_gams_version(self, version_string):
        major, minor, patch = self._version.split(".")
        self._major_rel_number = int(major)
        self._minor_rel_number = int(minor)
        self._gold_rel_number = int(patch)

    def _init_gams_version(self):
        # read version from gamsstmp.txt (fast)
        try:
            with open(os.path.join(self._system_directory, "gamsstmp.txt"), "r") as f:
                self._version = f.read()
            # wei 48.1.0 (Oct 12, 2024): Sat 12 Oct 11:24:04 AM EST 2024
            self._version = self._version.split()[1].strip()
            self._parse_gams_version(self._version)
        except:  # we could not derive the version from gamsstmp.txt, try 'gams audit' instead (slow)
            if self._debug >= DebugLevel.Verbose:
                warn(f"Unable to read version information from gamsstmp.txt. Switching to 'gams audit' which which might result in decreased performance.", stacklevel=2)
            self._version = self._run_gams_audit()
            try:
                # GAMSX            24.1.0 r38765 ALFA Released  1Mar13 VS8 x86/MS Windows
                self._version = self._version.split()[1].strip()
                self._parse_gams_version(self._version)
            # for compatibility with GAMS version before 24.1
            except:
                #e.g. GAMSX            Feb 14, 2013 24.0.2 WIN 38380.38394 VS8 x86/MS Windows
                self._version = self._version.split()[4].strip()
                self._parse_gams_version(self._version)

    def __init__(self, working_directory=None, system_directory=None, debug=DebugLevel.KeepFilesOnError):
        '''
        @brief constructor
        @param working_directory GAMS working directory, anchor for all file-based operations (determined automatically if omitted, in user's temporary folder)
        @param system_directory  GAMS system directory (determined automatically if omitted)
        @param debug Debug Flag (default: DebugLevel.KeepFilesOnError)
        '''

        self._debug = debug
        self._has_error = False

        # Allow to overwrite Debug setting with environment variable
        if "GAMSOOAPIDEBUG" in os.environ:
            env_debug = os.environ["GAMSOOAPIDEBUG"].lower()
            if env_debug == "off": self._debug = DebugLevel.Off
            elif env_debug == "keepfilesonerror": self._debug = DebugLevel.KeepFilesOnError
            elif env_debug == "keepfiles": self._debug = DebugLevel.KeepFiles
            elif env_debug == "showlog": self._debug = DebugLevel.ShowLog
            elif env_debug == "verbose": self._debug = DebugLevel.Verbose

        self._checkpoint_lock = threading.Lock()
        self._database_lock = threading.Lock()
        self._job_lock = threading.Lock()
        self._modelinstance_lock = threading.Lock()
        self._debug_lock = threading.Lock()

        self._debug_out("---- Entering GamsWorkspace constructor ----", 0)

        self._system_directory = None
        self._working_directory = None
        self._using_tmp_working_dir = None

        self._eps = None

        self._gmdHandles = []
        self._gevHandles = []

        ## @brief A string used to prefix automatically generated files
        self.scratch_file_prefix = "_gams_py_"

        # TODO: can we use lists instead of dictionaries?
        self._gams_checkpoints = {}
        self._gams_databases = {}
        self._gams_jobs = {}
        self._gams_modelinstances = {}

        self._def_job_name_cnt = 0
        self._def_job_name_stem = "gjo"

        self._def_database_name_cnt = 0
        self._def_database_name_stem = "gdb"

        self._def_checkpoint_name_cnt = 0
        self._def_checkpoint_name_stem = "gcp"

        self._def_modelinstance_name_cnt = 0
        self._def_modelinstance_name_stem = "gmi"

        if working_directory is None:
            self._using_tmp_working_dir = True
            self._working_directory = tempfile.mkdtemp()
        else:
            if working_directory == "":
                raise GamsException("Empty string is not allowd as working directory")
            self._working_directory = os.path.abspath(working_directory)
            # if the directory doesn't exist, create it
            if not os.path.exists(self._working_directory):
                os.mkdir(self._working_directory)

        if _is_win:
            if system_directory is None:
                self._system_directory = GamsWorkspace._find_gams_win()
                if not self._system_directory or not os.path.exists(os.path.join(os.path.abspath(self._system_directory), "optgams.def")):
                    raise GamsException("GAMS System directory " + self._system_directory + " not found or invalid. Either specify a valid system directory by passing it to the GamsWorkspace constructor or run findthisgams.exe in the GAMS system directory you want to use.")

            else:
                if system_directory == "":
                    raise GamsException("Empty string is not allowd as system directory")
                self._system_directory = os.path.abspath(system_directory)
                if not os.path.exists(os.path.join(self._system_directory, "optgams.def")):
                    raise GamsException("Invalid GAMS system directory: " + self._system_directory)
        else:
            if system_directory is None:
                if _is_linux: ld_string = "LD_LIBRARY_PATH"
                elif _is_osx: ld_string = "DYLD_LIBRARY_PATH"
                path = GamsWorkspace._find_ld_library_path("PATH")
                ld_library_path = GamsWorkspace._find_ld_library_path(ld_string)

                if path and os.path.exists(os.path.join(os.path.abspath(path), "optgams.def")):
                    self._system_directory = path
                elif ld_library_path and os.path.exists(os.path.join(os.path.abspath(ld_library_path), "optgams.def")):
                    self._system_directory = ld_library_path
                else:
                    raise GamsException("GAMS System directory not found or invalid. You need to set either PATH or " + ld_string + " to a valid GAMS system directory or to specify one in the GamsWorkspace constructor.")

                if self._debug > DebugLevel.KeepFilesOnError:
                    if not GamsWorkspace.is_same_system_directory(os.path.abspath(path), os.path.abspath(ld_library_path)):
                        warn(f"Found different GAMS system directories in PATH and {ld_string}. Using the one from PATH", stacklevel=2)
            else:
                if system_directory == "":
                    raise GamsException("Empty string is not allowd as system directory")
                self._system_directory = os.path.abspath(system_directory)
                if not os.path.exists(os.path.join(self._system_directory, "optgams.def")):
                    raise GamsException("Invalid GAMS system directory: " + self._system_directory)
        self._system_directory = os.path.realpath(os.path.abspath(self._system_directory))

        prefix = ""
        suffix = ".dll"
        if _is_linux:
            prefix = "lib"
            suffix = ".so"
        elif _is_osx:
            prefix = "lib"
            suffix = ".dylib"

        #Check that none of the required GAMS libraries can be found in the working directory
        if os.path.normcase(self._system_directory) != os.path.normcase(self._working_directory):
            libstems = ["gdxcc", "gdxdc", "gmdcc", "joatdc", "optdc"]
            for stem in libstems:
                lib_name = prefix + stem + "lib64" + suffix
                if os.path.exists (os.path.join(self._working_directory, lib_name)):
                    warn(
                        f"Found library {lib_name} "
                        + f"in the Working Directory ({self._working_directory}). "
                        + f"This could cause a problem when it is a different version than the one in the System Directory ({self._system_directory}).",
                        stacklevel=2
                    )

        # need to set the path for windows
        if _is_win:
            # GamsJob.run_engine() requires urllib3 which loads libssl-1_1-x64.dll. We need to import urllib3
            # before we prepend the GAMS system directory to the PATH in order to prevent loading an incompatible version
            # of libssl-1_1-x64.dll from the GAMS system directory.
            try:
                import urllib3
            except:
                pass
            env_var = "PATH"
            if env_var in os.environ:
                if not os.environ[env_var].startswith(self._system_directory + os.pathsep):
                    os.environ[env_var] = self._system_directory + os.pathsep + os.environ[env_var]
            else:
               os.environ[env_var] = self._system_directory

        self._init_gams_version()
        if self._version !=  GamsOptions._api_ver:
            warn(f"The GAMS version ({self.version}) differs from the API version ({GamsOptions._api_ver}).", stacklevel=2)

    def _debug_out(self, msg, lvl):
        self._debug_lock.acquire()
        if self._debug >= DebugLevel.Verbose:
            for i in range(lvl):
                print("  ", end="")
            print(msg)
            sys.stdout.flush()
        self._debug_lock.release()

    def __del__(self):
        self._debug_out("---- Entering GamsWorkspace destructor ----", 0)
        for g in self._gmdHandles:
            if gmdHandleToPtr(g) != None:
                gmdFree(g)
        for g in self._gevHandles:
            if gevHandleToPtr(g) != None:
                gevFree(g)
        try:
            if self._using_tmp_working_dir and (self._debug == DebugLevel.Off or (self._debug == DebugLevel.KeepFilesOnError and not self._has_error)):
                shutil.rmtree(self._working_directory)
        except:
            pass

    def _xxxlib(self, libname, model):
        if _is_win:
            p = Popen(self._system_directory + os.sep + libname + "lib.exe " + model, cwd=self._working_directory)
        else:
            p = Popen([self._system_directory + os.sep + libname + "lib", model], cwd=self._working_directory)
        exitcode = p.wait()
        if  exitcode != 0:
            raise GamsException(libname + "lib return code not 0 (" + str(exitcode) + ")")

    def gamslib(self, model):
        '''
        @brief Retrieves model from GAMS Model Library
        @param model Model name
        '''
        self._xxxlib("gams", model)

    def testlib(self, model):
        '''
        @brief Retrieves model from GAMS Test Library
        @param model Model name
        '''
        self._xxxlib("test", model)

    def emplib(self, model):
        '''
        @brief Retrieves model from Extended Math Programming Library
        @param model Model name
        '''
        self._xxxlib("emp", model)

    def datalib(self, model):
        '''
        @brief Retrieves model from GAMS Data Utilities Library
        @param model Model name
        '''
        self._xxxlib("data", model)

    def finlib(self, model):
        '''
        @brief Retrieves model from Practical Financial Optimization Library
        @param model Model name
        '''
        self._xxxlib("fin", model)

    def noalib(self, model):
        '''
        @brief Retrieves model from Nonlinear Optimization Applications Using the GAMS Technology Library
        @param model Model name
        '''
        self._xxxlib("noa", model)

    def psoptlib(self, model):
        '''
        @brief Retrieves model from Power System Optimization Modelling Library
        @param model Model name
        '''
        self._xxxlib("psopt", model)

    def apilib(self, model):
        '''
        @brief Retrieves model from GAMS API Library
        @param model Model name
        '''
        self._xxxlib("api", model)

    def add_database(self, database_name=None, source_database=None, in_model_name = None):
        '''
        @brief Database creation
        @param database_name Identifier of GamsDatabase (determined automatically if omitted)
        @param source_database Source GamsDatabase to initialize Database from (empty Database if omitted)
        @param in_model_name GAMS string constant that is used to access this database
        @return Instance of type GamsDatabase
        '''
        return GamsDatabase(self, database_name, None, source_database, in_model_name)

    def add_database_from_gdx(self, gdx_file_name, database_name=None, in_model_name = None):
        '''
        @brief Database creation from an existing GDX file
        @param gdx_file_name GDX File to initialize Database from
        @param database_name Identifier of GamsDatabase (determined automatically if omitted)
        @param in_model_name GAMS string constant that is used to access this database
        @return Instance of type GamsDatabase
        '''
        if gdx_file_name == None or len(gdx_file_name) == 0:
            raise GamsException("Could not create GamsDatabase instance with gdx_file_name being None or empty string")
        return GamsDatabase(self, database_name, gdx_file_name, None, in_model_name)

    def _add_database_from_gmd(self, gmd_handle, database_name=None, in_model_name = None):
        '''
        @brief Database creation from an existing GMD handle. This will alter setting for special values and debug settings using the functions: gmdSetDebug and gmdSetSpecialValues. Meant for internal use only
        @param gmd_handle The already created and initialised GMD handle
        @param database_name Identifier of GamsDatabase (determined automatically if omitted)
        @param in_model_name GAMS string constant that is used to access this database
        @return Instance of type GamsDatabase
        '''
        return GamsDatabase(self, database_name, None, None, in_model_name, False, gmd_handle)

    def add_job_from_string(self, gams_source, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from string model source
        @param gams_source GAMS model as string
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        return GamsJob(self, source=gams_source, checkpoint=checkpoint, job_name=job_name)

    def add_job_from_file(self, file_name, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model file
        @param file_name GAMS source file name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        return GamsJob(self, file_name=file_name, checkpoint=checkpoint, job_name=job_name)

    def add_job_from_gamslib(self, model, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model from GAMS Model Library
        @param model model name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        self.gamslib(model)
        return GamsJob(self, file_name=model+".gms", checkpoint=checkpoint, job_name=job_name)

    def add_job_from_testlib(self, model, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model from GAMS Test Library
        @param model model name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        self.testlib(model)
        return GamsJob(self, file_name=model+".gms", checkpoint=checkpoint, job_name=job_name)

    def add_job_from_apilib(self, model, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model from GAMS API Library
        @param model model name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        self.apilib(model)
        return GamsJob(self, file_name=model+".gms", checkpoint=checkpoint, job_name=job_name)

    def add_job_from_emplib(self, model, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model from GAMS Extended Math Programming Library
        @param model model name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        self.emplib(model)
        return GamsJob(self, file_name=model+".gms", checkpoint=checkpoint, job_name=job_name)

    def add_job_from_datalib(self, model, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model from GAMS Data Utilities Library
        @param model model name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        self.datalib(model)
        return GamsJob(self, file_name=model+".gms", checkpoint=checkpoint, job_name=job_name)

    def add_job_from_finlib(self, model, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model from Practical Financial Optimization Library
        @param model model name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        self.finlib(model)
        return GamsJob(self, file_name=model+".gms", checkpoint=checkpoint, job_name=job_name)

    def add_job_from_noalib(self, model, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model from GAMS Non-linear Optimization Applications Library
        @param model model name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        self.noalib(model)
        return GamsJob(self, file_name=model+".gms", checkpoint=checkpoint, job_name=job_name)

    def add_job_from_psoptlib(self, model, checkpoint=None, job_name=None):
        '''
        @brief Create GamsJob from model from Power System Optimization Modelling Library
        @param model model name
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        @return GamsJob instance
        '''
        self.psoptlib(model)
        return GamsJob(self, file_name=model+".gms", checkpoint=checkpoint, job_name=job_name)

    def add_options(self, gams_options_from=None, opt_file=None):
        '''
        @brief Create GamsOptions
        @param gams_options_from GamsOptions used to initialize the new object
        @param opt_file Parameter file used to initialize the new object
        @return GamsOptions instance
        '''
        if gams_options_from and opt_file:
            raise GamsException("Specify either gams_options_from or opt_file but not both")
        return GamsOptions(self, gams_options_from, opt_file)

    def add_checkpoint(self, checkpoint_name=None):
        '''
        @brief Create GamsCheckpoint
        @param checkpoint_name checkpoint_name Identifier of GamsCheckpoint or filename for existing checkpoint (determined automatically if omitted)
        @return GamsCheckpoint instance
        '''
        return GamsCheckpoint(self, checkpoint_name)

    def _job_add(self, job_name=None):
        if not job_name:
            self._job_lock.acquire()
            name = self.scratch_file_prefix + self._def_job_name_stem + str(self._def_job_name_cnt);
            while name in self._gams_jobs:
                self._def_job_name_cnt += 1
                name = self.scratch_file_prefix + self._def_job_name_stem + (self._def_job_name_cnt)
            self._def_job_name_cnt+=1

            self._gams_jobs[name] = self._def_job_name_cnt - 1
            self._job_lock.release()
            return name
        else:
            self._job_lock.acquire()
            if job_name in self._gams_jobs:
                self._job_lock.release()
                return False
            else:
                self._gams_jobs[job_name] = 0
            self._job_lock.release()
            return True

    def _database_add(self, database_name=None):
        if not database_name:
            self._database_lock.acquire()
            name = self.scratch_file_prefix + self._def_database_name_stem + str(self._def_database_name_cnt);
            while name in self._gams_databases:
                self._def_database_name_cnt +=1
                name = self.scratch_file_prefix + self._def_database_name_stem + (self._def_database_name_cnt)
            self._def_database_name_cnt+=1


            self._gams_databases[name] = self._def_database_name_cnt - 1
            self._database_lock.release()
            return name
        else:
            self._database_lock.acquire()
            if database_name in self._gams_databases:
                self._database_lock.release()
                return False
            else:
                self._gams_databases[database_name] = 0
            self._database_lock.release()
            return True

    def _checkpoint_add(self, checkpoint_name=None):
        if not checkpoint_name:
            self._checkpoint_lock.acquire()
            name = self.scratch_file_prefix + self._def_checkpoint_name_stem + str(self._def_checkpoint_name_cnt);
            while name in self._gams_checkpoints:
                self._def_checkpoint_name_cnt += 1
                name = self.scratch_file_prefix + self._def_checkpoint_name_stem + (self._def_checkpoint_name_cnt)
            self._def_checkpoint_name_cnt+=1

            self._gams_checkpoints[name] = self._def_checkpoint_name_cnt - 1
            self._checkpoint_lock.release()
            return name
        else:
            self._checkpoint_lock.acquire()
            if checkpoint_name in self._gams_checkpoints:
                self._checkpoint_lock.release()
                return False
            else:
                self._gams_checkpoints[checkpoint_name] = 0
            self._checkpoint_lock.release()
            return True

    def _modelinstance_add(self, modelinstance_name=None):
        if not modelinstance_name:
            self._modelinstance_lock.acquire()
            name = self.scratch_file_prefix + self._def_modelinstance_name_stem + str(self._def_modelinstance_name_cnt);
            while name in self._gams_modelinstances:
                self._def_modelinstance_name_cnt += 1
                name = self.scratch_file_prefix + self._def_modelinstance_name_stem + (self._def_modelinstance_name_cnt)
            self._def_modelinstance_name_cnt+=1

            self._gams_modelinstances[name] = self._def_modelinstance_name_cnt - 1
            self._modelinstance_lock.release()
            return name
        else:
            self._modelinstance_lock.acquire()
            if modelinstance_name in self._gams_modelinstances:
                self._modelinstance_lock.release()
                return False
            else:
                self._gams_modelinstances[modelinstance_name] = 0
            self._modelinstance_lock.release()
            return True

    def _job_delete(self, job_name):
        self._job_lock.acquire()
        try:
            del self._gams_jobs[job_name]
            return True
        except KeyError:
            return False

    def _database_delete(self, database_name):
        self._database_lock.acquire()
        try:
            del self._gams_databases[database_name]
            return True
        except KeyError:
            return False

    def _checkpoint_delete(self, checkpoint_name):
        self._checkpoint_lock.acquire()
        try:
            del self._gams_checkpoints[checkpoint_name]
            return True
        except KeyError:
            return False

    def _modelinstance_delete(self, modelinstance_name):
        self._modelinstance_lock.acquire()
        try:
            del self._gams_modelinstances[modelinstance_name]
            return True
        except KeyError:
            return False

    def _opt_file_extension(self, optfile):
        if optfile < 2:
            return "opt"
        elif optfile < 10:
            return "op" + str(optfile)
        elif optfile < 100:
            return "o" + str(optfile)
        elif optfile <=999:
            return "" + str(optfile)
        else:
            raise GamsException("Index Out of Bounds when writing opt file, must be between 1 and 999, saw " + str(optfile))

