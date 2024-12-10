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


#TODO: use from os import * to avoid that os is available automatically when importing gams!
from gams.core.opt import *
from gams.core.gmo import *
from gams.core.cfg import *
from gams.core.gev import *
from gams.control.options import *
from gams.control.database import *
import gams.control.workspace

import json
import os
import tempfile
import shutil
import subprocess
import sys
import time
import urllib.parse
import zipfile
import io
import base64
import copy


#TODO: should we move these enum types to the __init__.py of the module?
## @brief What field to update
class UpdateAction(object):
    ## @brief Supplies upper bounds for a variable
    Upper = 1
    ## @brief Supplies lower bounds for a variable
    Lower = 2
    ## @brief Supplies fixed bounds for a variable
    Fixed = 3
    ## @brief Supplies level for a variable or equation
    Primal = 4
    ## @brief Supplies marginal for a variable or equation
    Dual = 5

## @brief Symbol update type
class SymbolUpdateType(object):
    ## @brief If record does not exist use 0 (Zero)
    Zero = 0
    ## @brief If record does not exist use values from instantiation
    BaseCase = 1
    ## @brief If record does not exist use value from previous solve
    Accumulate = 2
    _Inherit = 3


class GamsEngineJob(object):
    def __init__(self, token, configuration, request_headers):
        '''
        @brief Constructor
        @param token Job token
        @param configuration GamsEngineConfiguration instance used to submit job
        '''
        self._token = token
        self._configuration = configuration
        self._request_headers = request_headers


class GamsEngineConfiguration(object):
    '''
    @brief Configuration that allows the execution of jobs on a specific GAMS Engine instance.
    @details
    '''

    def get_host(self):
        return self._host

    def set_host(self, host):
        validated_url = urllib.parse.urlparse(host)
        if validated_url.scheme not in ['http', 'https']:
            raise gams.control.workspace.GamsException("Invalid GAMS Engine host. Only HTTP and HTTPS protocols supported")
        if validated_url.netloc == '':
            raise gams.control.workspace.GamsException("Invalid GAMS Engine host. Make sure you provide a valid URL.")
        host = host.rstrip("/")
        if not host.endswith("/api"):
            host += "/api"
        self._host = host
    ## @brief Base url
    host = property(get_host, set_host)

    def get_username(self):
        return self._username

    def set_username(self, username):
        self._username = username
    ## @brief Username for HTTP basic authentication
    username = property(get_username, set_username)

    def get_password(self):
        return self._password

    def set_password(self, password):
        self._password = password
    ## @brief Password for HTTP basic authentication
    password = property(get_password, set_password)

    def get_jwt(self):
        return self._jwt

    def set_jwt(self, jwt):
        self._jwt = jwt
    ## @brief JWT token to use for Bearer authentication. Will only be used if username is empty.
    jwt = property(get_jwt, set_jwt)

    def get_namespace(self):
        if not self._namespace:
            raise gams.control.workspace.GamsException(
                "No GAMS Engine namespace set.")
        return self._namespace

    def set_namespace(self, namespace):
        self._namespace = namespace
    ## @brief Namespace in which the job is to be executed
    namespace = property(get_namespace, set_namespace)

    def _get_auth_header(self):
        '''Returns authentication header'''
        if not self.username:
            if not self.jwt:
                raise gams.control.workspace.GamsException("Neither username/password nor JWT token provided for authentication with the GAMS Engine instance.")
            return "Bearer " + self.jwt
        return "Basic " + base64.b64encode((self.username + ':' + self.password).encode("utf-8")).decode("utf-8")

    def __init__(self, host=None, username=None, password=None, jwt=None, namespace=None):
        '''
        @brief Constructor
        @param host Base url
        @param username Username for HTTP basic authentication
        @param password Password for HTTP basic authentication
        @param jwt JWT token to use for Bearer authentication. Will only be used if username is empty.
        @param namespace Namespace in which the job is to be executed
        '''
        self._jwt = ''
        self._username = ''
        self._password = ''
        self.set_host(host)
        self.set_username(username)
        self.set_password(password)
        self.set_jwt(jwt)
        self.set_namespace(namespace)


class GamsModifier(object):
    '''
    @brief Instances of this class are input to GamsModelInstance.instantiate()
    @details A GamsModifier consists either
             of a GamsParameter or a triple: A GamsVariable or GamsEquation to be modified, the modification
             action (e.g. . Upper, Lower or Fixed for updating bounds of a variable, or Primal/Dual for updating
             the level/marginal of a variable or equation mainly used for starting non-linear models from different
             starting points), and a GamsParameter that holds the data for modification. In addition the UpdateType
             can be defined (if ommitted the type defined in the Solve call is used).
    '''
    def get_gams_symbol(self):
        return self._gams_symbol
    ## @brief Symbol in the GAMS model to be modified
    gams_symbol = property(get_gams_symbol)

    def get_update_action(self):
        return self._update_action
    ## @brief Type of modification
    update_action = property(get_update_action)

    def get_data_symbol(self):
        return self._data_symbol
    ## @brief Symbol containing the data for the modification
    data_symbol = property(get_data_symbol)

    def get_update_type(self):
        return self._update_type
    ## @brief Symbol Update Type
    update_type = property(get_update_type)

    def __init__(self, gams_symbol, update_action=None, data_symbol=None, update_type = SymbolUpdateType._Inherit):
        '''
        @brief Constructor
        @param gams_symbol Symbol in the GAMS model to be modified.
                           This can be a GamsParameter, GamsVariable or GamsEquation.
                           If a variable or an equation is specified a data_symbol and
                           an update_action have to be specified as well.
        @param update_action Modification action
        @param data_symbol Parameter containing the data for the modification
        @param update_type Symbol Update Type (default: Inherit from model instance)
        '''
        self._update_action = None
        # update_action and data_symbol specified
        if update_action and data_symbol != None:
            if gams_symbol._dim != data_symbol._dim:
                raise gams.control.workspace.GamsException("GAMS Symbol and Data must have same dimension, but saw " + gams_symbol._dim + " (GAMS Symbol) and " + data_symbol._dim + " (Data)");
            if gams_symbol._database != data_symbol._database:
                raise gams.control.workspace.GamsException("GAMS Symbol and Data must belong to same GAMSDatabase");

            if update_action == UpdateAction.Upper or update_action == UpdateAction.Lower or update_action == UpdateAction.Fixed:
                if not isinstance(gams_symbol, GamsVariable):
                    #TODO: thiswill just print the interger of the constant
                    raise gams.control.workspace.GamsException("GAMS Symbol must be GAMSVariable for " + update_action)
            elif update_action == UpdateAction.Primal or update_action == UpdateAction.Dual:
                if not (isinstance(gams_symbol, GamsVariable) or isinstance(gams_symbol, GamsEquation)):
                    raise gams.control.workspace.GamsException("GAMS Symbol must be GAMSVariable or GAMSEquation for " + update_action)
            else:
                raise gams.control.workspace.GamsException("Unknown update action " + update_action)
            self._gams_symbol = gams_symbol
            self._update_action = update_action
            self._data_symbol = data_symbol
        # only the gams_symbol is specified
        elif update_action == None and data_symbol == None:
            self._gams_symbol = gams_symbol
            self._data_symbol = None
        else:
            raise gams.control.workspace.GamsException("Wrong combination of parameters. Specifying only update_action or data_symbol is not allowed.")
        self._update_type = update_type
## @brief The GamsModelInstanceOpt can be used to customize the GamsModelInstance.solve() routine.
class GamsModelInstanceOpt:
    def __init__(self, solver=None, opt_file=-1, no_match_limit=0, debug=False):
        '''
        @brief Constructor
        @param solver GAMS Solver
        @param opt_file GAMS option file number
        @param no_match_limit Controls the maximum number of accepted unmatched scenario records before terminating the solve
        @param debug Debug Flag
        '''
        ## @brief GAMS Solver
        self.solver = solver
        ## @brief GAMS Optionfile number
        self.opt_file = opt_file
        ## @brief Controls the maximum number of accepted unmatched scenario records before terminating the solve
        self.no_match_limit = no_match_limit
        ## @brief Debug Flag
        self.debug = debug

class GamsModelInstance(object):
    '''
    @brief
    @details <p>The GamsJob class is the standard way of dealing with a GAMS model and the
             corresponding solution provided by a solver. The GAMS language provides
             programming flow that allows to solve models in a loop and do other
             sophisticated tasks, like building decomposition algorithms.</p>
             <p>In rare cases, the GAMS model generation time dominates the solver solution time
             and GAMS itself becomes the bottleneck in an optimization application. For a
             model instance which is a single mathematical model generated by a GAMS solve
             statement, the GamsModelInstance class provides a controlled way of modifying a
             model instance and solving the resulting problem in the most efficient way, by
             communicating only the changes of the model to the solver and doing a hot start
             (in case of a continuous model like LP) without the use of disk IO.</p>
             <p>The GamsModelInstance requires a GamsCheckpoint that contains the model
             definition. Significant parts of the GAMS solve need to be provided for the
             instantiation of the GamsModelInstance. The modification of the model instance is
             done through data in sync_db (a property of GamsModelInstance of type GamsDatabase).
             One needs to create GamsModifiers which contain the information on how to modify
             the GamsModelInstance. Such a GamsModifier consists either of a GamsParameter or
             of a triple with the GamsVariable or GamsEquation to be updated, the modification
             action (e.g. Upper, Lower or Fixed for updating bounds of a variable, or Primal/Dual
             for updating the level/marginal of a variable or equation mainly used for starting
             non-linear models from different starting points), and a GamsParameter that holds
             the data for modification. GamsSymbols of a GamsModifier must belong to sync_db.
             The list of GamsModifiers needs to be supplied on the instantiate call. The use of
             GamsParameters that are GamsModifiers is restricted in the GAMS model source. For
             example, the parameter cannot be used inside $(). Such parameters become endogenous
             to the model and will be treated by the GAMS compiler as such. Moreover, the rim of
             the model instance is fixed: No addition of variables and equations is possible.</p>
             <p>The instantiate call will only query the symbol information of the GamsModifiers,
             not the data of sync_db, e.g. to retrieve the dimension of the modifiers. That's why
             the modifier symbols have to exist (but don't have to have data) in sync_db when
             instantiate is called. The GamsParameters that contain the update data in sync_db can
             be filled at any time before executing the solve method. The solve method uses this
             data to update the model instance. The solve method will iterate through all records
             of modifier symbols in the model instance and try to find update data in sync_db. If
             a record in sync_db is found, this data record will be copied into the model instance.
             If no corresponding record is found in SyncDB there are different choices: 1) the
             original data record is restored (update_type=SymbolUpdateType.BaseCase) which is the default, 2) the
             default record of a GamsParameter (which is 0)  is used (update_type=SymbolUpdateType.Zero, and 3) no
             copy takes place and we use the previously copied record value (update_type=SymbolUpdateType.Accumulate).
             After the model instance has been updated, the model is passed to the selected solver.</p>
             <p>After the completion of the Solve method, the sync_db will contain the primal and
             dual solution of the model just solved. Moreover, the GamsParameters that are
             GamsModifiers are also accessible in sync_db as GamsVariables with the name of the
             GamsParameter plus "_var". The Marginal of this GamsVariable can provide sensitivity
             information about the parameter setting. The status of the solve is accessible through
             the model_status and solver_status properties.</p>
             <p>In general, file operations in GAMS Python API take place in the working_directory
             defined in the GamsWorkspace. Exceptions to this rule are files read or created
             due to solver specific options in the solve routine of GamsModelInstance. These files
             are written to (or read from) the current directory, meaning the directory where
             the application gets executed.</p>

             Example on how to create a GAMSModelInstance from a GAMSCheckpoint that was
             generated by the Run method of GAMSJob.
             @code{.py}
             ws = GamsWorkspace()
             cp = ws.add_checkpoint()

             ws.gamslib("trnsport")

             job = ws.add_job_from_file("trnsport.gms")
             job.run(checkpoint=cp)

             mi = cp.add_modelinstance()
             b = mi.sync_db.add_parameter("b", 1, "demand")

             mi.instantiate("transport us lp min z", GamsModifier(b))

             bmult = [ 0.7, 0.9, 1.1, 1.3 ]
             for bm in bmult:
                 b.clear()
                 for rec in job.out_db.get_parameter("b"):
                     b.add_record(rec.keys).value = rec.value * bm
                 mi.solve()
                 print("Scenario bmult=" + str(bm) + ":")
                 print("  Modelstatus: " + str(mi.model_status))
                 print("  Solvestatus: " + str(mi.solver_status))
                 print("  Obj: " + str(mi.sync_db.get_variable("z")[()].level))
             @endcode
    '''

    #TODO: this will just return the integer values. In C# we receive some enum item type.
    def get_model_status(self):
        return gmoModelStat(self._gmo)
    ## @brief Status of the model. (available after a solve)
    model_status = property(get_model_status)

    def get_solver_status(self):
        return gmoSolveStat(self._gmo)
    ## @brief Solve status of the model. (available after a solve)
    solver_status = property(get_solver_status)

    def get_checkpoint(self):
        return self._checkpoint
    ## @brief Retrieve GamsCheckpoint
    checkpoint = property(get_checkpoint)

    def get_name(self):
        return self._modelinstance_name
    ## @brief Retrieve name of GamsModelInstance
    name = property(get_name)

    def get_sync_db(self):
        return self._sync_db
    ## @brief Retrieve GamsDatabase used to synchronize modifiable data
    sync_db = property(get_sync_db)


    def __init__(self, checkpoint=None, modelinstance_name=None, source=None):
        '''
        @brief Constructor
        @param checkpoint GamsCheckpoint
        @param modelinstance_name Identifier of GamsModelInstance (determined automatically if omitted)
        @param source model instance to be copied
        '''

        self._gmo = None
        self._gev = None
        # copy constructor
        if source:
            self._checkpoint = source._checkpoint
            if not source._instantiated:
                raise gams.control.workspace.GamsException("Source GamsModelInstance not instantiated, cannot copy from it")

            if not modelinstance_name:
                self._modelinstance_name = source._checkpoint.workspace._modelinstance_add()
            else:
                if not source._checkpoint.workspace._modelinstance_add(modelinstance_name):
                    raise gams.control.workspace.GamsException("ModelInstance with name " + modelinstance_name + " already exists")
                self._modelinstance_name = modelinstance_name
            source._checkpoint._workspace._debug_out("---- Entering GamsModelInstance constructor ----", 0)

            self._scr_dir = os.path.join(self._checkpoint.workspace.working_directory, self._modelinstance_name)
            if os.path.exists(self._scr_dir):
                try:
                    shutil.rmtree(self._scr_dir, True)
                except:
                    pass

            self._sync_db = self._checkpoint.workspace.add_database(source_database = source.sync_db)

            self._gev = new_gevHandle_tp()
            ret = gevCreateD(self._gev, self._checkpoint._workspace._system_directory, GMS_SSSIZE)
            if not ret[0]:
                raise gams.control.workspace.GamsException(ret[1])
            self._checkpoint._workspace._gevHandles.append(self._gev)

            self._gmo = new_gmoHandle_tp()
            ret = gmoCreateD(self._gmo, self._checkpoint._workspace._system_directory, GMS_SSSIZE)
            if not ret[0]:
                raise gams.control.workspace.GamsException(ret[1])

            self._modifiers = []

            for mod in source._modifiers:
                if not mod._data_symbol: #Parameter
                    self._modifiers.append(GamsModifier(self.sync_db.get_parameter(mod._gams_symbol.name), update_type=mod._update_type))
                elif isinstance(mod._gams_symbol, GamsVariable):
                    self._modifiers.append(GamsModifier(self.sync_db.get_variable(mod._gams_symbol.name), mod._update_action, self.sync_db.get_parameter(mod._data_symbol.name), mod._update_type))
                elif isinstance(mod._gams_symbol, GamsEquation):
                    self._modifiers.append(GamsModifier(self.sync_db.get_equation(mod._gams_symbol.name), mod._update_action, self.sync_db.get_parameter(mod._data_symbol.name), mod._update_type))
                else:
                    raise gams.control.workspace.GamsException("Unexpected Symbol as Modifier")

            ret = gevDuplicateScratchDir(source._gev, self._scr_dir, os.path.join(self._scr_dir, "gamslog.dat"))
            if ret[0] != 0:
                raise gams.control.workspace.GamsException("Problem duplicating scratch directory")

            if gevInitEnvironmentLegacy(self._gev, ret[1]) != 0:
                raise gams.control.workspace.GamsException("Could not initialize model instance")

            gmoRegisterEnvironment(self._gmo, gevHandleToPtr(self._gev))
            ret = gmoLoadDataLegacy(self._gmo)
            if ret[0] != 0:
                raise gams.control.workspace.GamsException("Could not load model instance: " + ret[1])

            rc = gmdRegisterGMO(self.sync_db._gmd, gmoHandleToPtr(self._gmo))
            self.sync_db._check_for_gmd_error(rc)

            self._log_available = source._log_available
            self._selected_solver = source._selected_solver

            opt_file_name = gmoNameOptFile(source._gmo)
            gmoNameOptFileSet(self._gmo, os.path.join(os.path.dirname(opt_file_name), self._selected_solver + os.path.splitext(opt_file_name)[1]))

            self._instantiated = True
            # Lock syncDB symbols so user can't add new symbols which would result in other exceptions
            self.sync_db._symbol_lock = True
            # Unlock syncDB record so user can add data for modifiers
            self.sync_db._record_lock = False

        else:
            if not modelinstance_name:
                self._modelinstance_name = checkpoint._workspace._modelinstance_add()
            else:
                if not checkpoint._workspace._modelinstance_add(modelinstance_name):
                    raise gams.control.workspace.GamsException("ModelInstance with name " + modelinstance_name + " already exists")
                self._modelinstance_name = modelinstance_name
            checkpoint._workspace._debug_out("---- Entering GamsModelInstance constructor ----", 0)

            self._p = None
            self._checkpoint = checkpoint
            self._scr_dir = self._checkpoint._workspace._working_directory + os.sep + self._modelinstance_name
            self._sync_db = GamsDatabase(self._checkpoint._workspace)
            self._sync_db._record_lock = True

            self._gev = new_gevHandle_tp()
            ret = gevCreateD(self._gev, self._checkpoint._workspace._system_directory, GMS_SSSIZE)
            if not ret[0]:
                raise gams.control.workspace.GamsException(ret[1])
            checkpoint._workspace._gevHandles.append(self._gev)

            self._gmo = new_gmoHandle_tp()
            ret = gmoCreateD(self._gmo, self._checkpoint._workspace._system_directory, GMS_SSSIZE)
            if not ret[0]:
                raise gams.control.workspace.GamsException(ret[1])

            self._modifiers = []
            self._instantiated = False

    def copy_modelinstance(self, modelinstance_name = None):
        '''
        @brief Copies this ModelInstance to a new ModelInstance
        @param modelinstance_name Identifier of GamsModelInstance (determined automatically if omitted)
        @return Reference to new ModelInstance
        '''

        return GamsModelInstance(modelinstance_name = modelinstance_name, source = self)

    ## @brief Use this to explicitly free unmanaged resources
    def __del__(self):
        self._checkpoint._workspace._debug_out("---- Entering GamsModelInstance destructor ----", 0)
        if self._gmo:
            gmoFree(self._gmo)
        if self._gev:
            if gevHandleToPtr(self._gev) != None:
                gevFree(self._gev)

    def cleanup(self):
        '''
        @brief Explicitly closes the license session when using a license that
        limits the actual uses of GAMS. This method should only be called
        when the GamsModelInstance is not used anymore.
        '''
        gmdCloseLicenseSession(self.sync_db._gmd)

    def instantiate(self, model_definition, modifiers=[], options=None):
        '''
        @brief Instantiate the GamsModelInstance
        @param model_definition Model definition
        @param modifiers List of GamsModifiers
        @param options GamsOptions
        '''
        have_par = False

        tmp_opt = GamsOptions(self._checkpoint._workspace, options)

        if self._instantiated:
            raise gams.control.workspace.GamsException("ModelInstance " + self._modelinstance_name + " already instantiated")

        rc, ival, dval, sval = gmdInfo(self._sync_db._gmd, GMD_NRUELS)
        self._sync_db._check_for_gmd_error(rc)
        if ival>0:
            raise gams.control.workspace.GamsException("Sync_db of " + self._modelinstance_name + " with unique elements. No AddRecord allowed prior to Instantiate")

        if isinstance(modifiers, GamsModifier):
            modifiers = [modifiers]
        elif isinstance(modifiers, tuple):
            modifiers = list(modifiers)
        for mod in modifiers:
            if mod._gams_symbol._database != self._sync_db:
                raise gams.control.workspace.GamsException("Symbol " + mod.GamsSym.Name + " not part of SyncDB");
            self._modifiers.append(mod)
            if isinstance(mod._gams_symbol, GamsSet):
                raise gams.control.workspace.GamsException("Sets cannot be model modifiers")
            if isinstance(mod._gams_symbol, GamsParameter):
                have_par = True

        # Symbols in sync_db that are not modifier
        if len(modifiers) < len(self._sync_db):
            nr_parameters=0
            for sym in self._sync_db:
                if isinstance(sym, GamsParameter):
                    nr_parameters += 1
                #TODO: Should this check really be taken out? We use it deactivated for Timo at the moment
                #if isinstance(sym, GamsSet):
                #    raise workspace.gams.control.workspace.GamsException("GAMSSet not allowed in SyncDB: " + sym.name)

            if len(modifiers) < nr_parameters:
                for sym in self._sync_db:
                    if isinstance(sym, GamsParameter):
                        found = False
                        for mod in modifiers:
                            if sym._sym_ptr == mod.gams_symbol._sym_ptr:
                                found = True
                                break
                        if not found:
                            raise gams.control.workspace.GamsException("Parameter " + sym.name + " is not a modifier")

        model = "option limrow=0, limcol=0;\n"

        # transport use lp min[imizing] z
        # or
        # transport min[imizing] z use lp
        model_direction = model_definition.split()[1]
        model_type = ""
        if model_direction[0:3].lower() in ["min", "max"]:
            model_type = model_definition.split()[4]
        else:
            model_type = model_definition.split()[2]

        if have_par:
            model += "Set s__(*) /'s0'/;\n"
            for mod in modifiers:
                if isinstance(mod._gams_symbol, GamsParameter):
                    model += "Parameter s__" + mod._gams_symbol._name + "(s__"
                    for i in range(mod._gams_symbol._dim):
                        model += ",*"
                    model += "); s__" + mod._gams_symbol._name + "(s__"
                    for i in range(mod._gams_symbol._dim):
                        model += ",s__"
                    model += ") = Eps ;\n"

            model += "Set dict(*,*,*) /\n's__'.'scenario'.''"
            for mod in modifiers:
                if isinstance(mod._gams_symbol, GamsParameter):
                    model += ",\n'" + mod._gams_symbol._name + "'.'param'.'s__" + mod.gams_symbol._name + "'"
            model += "/;\n"

        model_name = model_definition.split(' ')[0]

        # .justScrDir was introduced with GAMS 34
        if self._checkpoint._workspace.major_rel_number < 34:
            raise gams.control.workspace.GamsException("GAMS 34 or newer is required to instantiate with this version of the API - Upgrade your GAMS version or switch to the API version that was shipped with the GAMS version you are using")

        model += model_name + ".justScrDir=1;\n"
        model += "solve " + model_definition

        if have_par:
            model += " scenario dict;"

        my_job = GamsJob(self._checkpoint._workspace, source=model, checkpoint=self._checkpoint)

        #TODO: use GAMSOptions class
        optSetStrStr(tmp_opt._opt, "ScrDir", self._scr_dir)
        if self._checkpoint._workspace._debug >= gams.control.workspace.DebugLevel.ShowLog:
            optSetIntStr(tmp_opt._opt, "LogOption", 4)
            self._log_available = False
        else:
            optSetIntStr(tmp_opt._opt, "LogOption", 2)
            self._log_available = True

        optSetStrStr(tmp_opt._opt, "LogFile", os.path.join(self._scr_dir, "gamslog.dat"))
        optSetStrStr(tmp_opt._opt, "SolverCntr", "gamscntr.dat")

        if not os.path.exists(self._scr_dir):
            os.mkdir(self._scr_dir)

        my_job.run(gams_options=tmp_opt, create_out_db=False)

        solver_cntr = optGetStrStr(tmp_opt._opt, "SolverCntr")
        if gevInitEnvironmentLegacy(self._gev, self._scr_dir + os.sep + solver_cntr) != 0:
            raise gams.control.workspace.GamsException("Could not initialize model instance")

        gmoRegisterEnvironment(self._gmo, gevHandleToPtr(self._gev))
        ret = gmoLoadDataLegacy(self._gmo)
        if ret[0] != 0:
            raise gams.control.workspace.GamsException("Could not load model instance: " + ret[1])

        self._selected_solver = tmp_opt._selected_solvers[gmoModelType(self._gmo)]
        opt_file_name = gmoNameOptFile(self._gmo)
        gmoNameOptFileSet(self._gmo, os.path.join(os.path.dirname(opt_file_name), self._selected_solver + os.path.splitext(opt_file_name)[1]))

        rc = gmdInitFromDict(self._sync_db._gmd, gmoHandleToPtr(self._gmo))
        self.sync_db._check_for_gmd_error(rc)

        del tmp_opt
        self._instantiated = True

        # Lock sync_db symbols so user can't add new symbols which would result in other exceptions
        self._sync_db._symbol_lock = True
        # Unlock sync_db record so user can add data for modifiers
        self._sync_db._record_lock = False


    def solve(self, update_type = SymbolUpdateType.BaseCase, output=None, mi_opt=None):
        '''
        @brief Solve model instance
        @param update_type Update type
        @param output Used to capture GAMS log, (e.g. sys.stdout or an object created by the build-in function open())
        @param mi_opt GamsModelInstance options
        '''

        if update_type not in [SymbolUpdateType.Zero, SymbolUpdateType.BaseCase, SymbolUpdateType.Accumulate]:
            raise gams.control.workspace.GamsException("Update type '" + str(update_type) + "' is not valid", self._checkpoint._workspace)
        no_match_limit = 0
        if mi_opt != None:
            no_match_limit = mi_opt.no_match_limit

        if not self._instantiated:
            raise gams.control.workspace.GamsException("Model instance " + self._model_instance_name + " not instantiated", self._checkpoint._workspace)
        rc = gmdInitUpdate(self._sync_db._gmd, gmoHandleToPtr(self._gmo))
        self.sync_db._check_for_gmd_error(rc, self._checkpoint._workspace)

        accumulate_no_match_cnt = 0
        no_match_cnt = 0

        for mod in self._modifiers:
            loc_sut = update_type
            if mod._update_type != SymbolUpdateType._Inherit:
                loc_sut = mod._update_type
            if isinstance(mod._gams_symbol, GamsParameter):
                rc, no_match_cnt = gmdUpdateModelSymbol(self._sync_db._gmd, mod._gams_symbol._sym_ptr, 0, mod._gams_symbol._sym_ptr, loc_sut, no_match_cnt)
                self.sync_db._check_for_gmd_error(rc, self._checkpoint._workspace)
            else:
                rc, no_match_cnt = gmdUpdateModelSymbol(self._sync_db._gmd, mod._gams_symbol._sym_ptr, mod._update_action, mod._data_symbol._sym_ptr, loc_sut, no_match_cnt)
                self.sync_db._check_for_gmd_error(rc, self._checkpoint._workspace)

            accumulate_no_match_cnt += no_match_cnt
            if accumulate_no_match_cnt > no_match_limit:
                raise gams.control.workspace.GamsException("Unmatched record limit exceeded while processing modifier " + mod._gams_symbol.name + ", for more info check GamsModelInstanceOpt parameter no_match_limit", self._checkpoint._workspace)

        # Close Log and status file and remove
        if self._log_available and output:
            gevSwitchLogStat(self._gev, 0, "", False, "", False, None, None, None)
            ls_handle = gevGetLShandle(self._gev)
            gevRestoreLogStatRewrite(self._gev, ls_handle);

        if output == sys.stdout:
            gevSwitchLogStat(self._gev, 3, gevGetStrOpt(self._gev, gevNameLogFile), False, gevGetStrOpt(self._gev, gevNameStaFile), False,  None, None, ls_handle)
            ls_handle = gevGetLShandle(self._gev)

        tmp_solver = self._selected_solver
        if mi_opt != None and mi_opt.solver:
            tmp_solver = mi_opt.solver

        tmp_opt_file = gmoOptFile(self._gmo)
        save_opt_file = tmp_opt_file
        save_name_opt_file = gmoNameOptFile(self._gmo)
        if mi_opt != None and mi_opt.opt_file != -1:
            tmp_opt_file = mi_opt.opt_file

        if mi_opt != None and mi_opt.debug:
            with open(os.path.join(self._checkpoint._workspace._working_directory, self._modelinstance_name, "convert.opt"), "w") as opt_file:
                opt_file.writelines([ "gams " + os.path.join(self._checkpoint._workspace._working_directory, self._modelinstance_name, "gams.gms"), \
                                      "dumpgdx " + os.path.join(self._checkpoint._workspace._working_directory, self._modelinstance_name, "dump.gdx\n"), \
                                      "dictmap " + os.path.join(self._checkpoint._workspace._working_directory, self._modelinstance_name, "dictmap.gdx") ])

                gmoOptFileSet(self._gmo, 1)
                gmoNameOptFileSet(self._gmo, os.path.join(self._checkpoint._workspace._working_directory, self._modelinstance_name, "convert.opt"))
                rc = gmdCallSolver(self._sync_db._gmd, "convert")
                self.sync_db._check_for_gmd_error(rc, self._checkpoint._workspace)

        gmoOptFileSet(self._gmo, tmp_opt_file);
        gmoNameOptFileSet(self._gmo, os.path.join(os.path.dirname(save_name_opt_file), tmp_solver + "." + self._checkpoint._workspace._opt_file_extension(tmp_opt_file)))

        rc = gmdCallSolver(self._sync_db._gmd, tmp_solver)
        self.sync_db._check_for_gmd_error(rc, self._checkpoint._workspace)

        gmoOptFileSet(self._gmo, save_opt_file)
        gmoNameOptFileSet(self._gmo, save_name_opt_file)

        if output == sys.stdout:
            gevRestoreLogStat(self._gev, ls_handle)

        if (output != None) and (output != sys.stdout):
            if self._log_available:
                gevSwitchLogStat(self._gev, 0, "", False, "", False, None, None, ls_handle)
                ls_handle = gevGetLShandle(self._gev)
                # TODO: in C# we open the file in some advanced mode to prevent from generating errors if the file is already open by some other resource
                with open(gevGetStrOpt(self._gev, gevNameLogFile)) as file:
                    for line in file.readlines():
                        output.write(line)
                    gevRestoreLogStat(self._gev, ls_handle)
            else:
                output.write("No solver log available")

    def interrupt(self):
        '''
        @brief Send interrupt signal to running GamsModelInstance
        '''
        gevTerminateRaise(self._gev)


class GamsCheckpoint(object):
    '''
    @brief A GamsCheckpoint class captures the state of a GamsJob after the GamsJob.run
           method has been carried out.
    @details Another GamsJob can continue (or restart) from a
    GamsCheckpoint. A GamsCheckpoint constructed with a file name will create a file
    (extension .g00) for permanent storage when supplied as parameter on the
    GamsJob.run method. Moreover, a GamsModelInstance is also initialized from a
    checkpoint that contains the model definition of the model instance.
    '''

    def get_workspace(self):
        return self._workspace
    ## @brief Get the GamsWorkspace
    workspace = property(get_workspace)

    def get_name(self):
        return self._name
    ## @brief Get the checkpoint name
    name = property(get_name)

    def __init__(self, workspace, checkpoint_name=None):
        '''
        @brief Constructor
        @param workspace GamsWorkspace containing GamsCheckpoint
        @param checkpoint_name Identifier of GamsCheckpoint (determined automatically if omitted)
        '''

        workspace._debug_out("---- Entering GamsCheckpoint constructor ----", 0)
        self._workspace = workspace
        if not checkpoint_name:
            self._name = self._workspace._checkpoint_add()
        else:
            if not self._workspace._checkpoint_add(checkpoint_name):
                raise gams.control.workspace.GamsException("Checkpoint with name " + checkpoint_name + " already exists")
            self._name = checkpoint_name
        if os.path.isabs(self._name):
            self._checkpoint_file_name = self._name
        else:
            self._checkpoint_file_name = self._workspace._working_directory + os.sep + self._name
        self._checkpoint_file_name = os.path.splitext(self._checkpoint_file_name)[0] + ".g00"

    def __del__(self):
        self._workspace._debug_out("---- Entering GamsCheckpoint destructor ----", 0)

    def add_modelinstance(self, modelinstance_name=None):
        '''
        @brief Create model instance
        @param modelinstance_name Identifier of GamsModelInstance (determined automatically if omitted)
        @return GamsModelInstance instance
        '''
        return GamsModelInstance(self, modelinstance_name=None)

class GamsJob(object):
    '''
    @brief The GamsJob class manages the execution of a GAMS program given by GAMS model
           source.
    @details <p>The GAMS source (or more precisely the root of a model source tree) of
             the job can be provided as a string or by a filename (relative to the working
             directory of the GamsWorkspace) of a text file containing the GAMS model source.
             The run method organizes the export of the input GamsDatabases, calls the GAMS
             compiler and execution system with the supplied options and on successful
             completion provides through the property out_db (of type GamsDatabase) the
             results of the model run.</p>
             <p>While the result data is captured in a GamsDatabase, the run method can also
             create a GamsCheckpoint that not only captures data but represents the state of
             the entire GamsJob and allows some other GamsJob to continue from this state.
             In case of a compilation or execution error, the run method will throw an
             exception. If the log output of GAMS is of interest, this can be captured by
             providing the output parameter of the run method (e.g. sys.stdout).</p>
    '''
    def get_job_name(self):
        return self._job_name
    ## @brief Retrieve name of GamsJob
    name = property(get_job_name)

    def get_workspace(self):
        return self._workspace
    ## @brief Get GamsWorkspace containing GamsJob
    workspace = property(get_workspace)

    def get_out_db(self):
        return self._out_db
    ## @brief Get GamsDatabase created by run method
    out_db = property(get_out_db)

    def __init__(self, ws, file_name=None, source=None, checkpoint=None, job_name=None):
        '''
        @brief Constructor
        @note It is not allowed to specify both file_name and source at the same time.
        @param ws GamsWorkspace containing GamsJob
        @param file_name GAMS source file name
        @param source GAMS model as string
        @param checkpoint GamsCheckpoint to initialize GamsJob from
        @param job_name Job name (determined automatically if omitted)
        '''

        ws._debug_out("---- Entering GamsJob constructor ----", 0)

        if file_name and source:
            raise gams.control.workspace.GamsException("Multiple sources specified: You can either set a file name or a source, but not both")

        self._workspace = ws
        self._job_name = None
        self._file_name = None

        if checkpoint != None and not os.path.exists(checkpoint._checkpoint_file_name):
            raise gams.control.workspace.GamsException("Checkpoint file " + checkpoint._checkpoint_file_name + " does not exist")

        self._checkpoint_start = checkpoint
        self._out_db = None
        self._http = None
        self._max_request_attempts = 3

        # handle job name
        if not job_name:
            self._job_name = self._workspace._job_add()
        else:
            self._job_name = job_name
            if not self._workspace._job_add(self._job_name):
                raise gams.control.workspace.GamsException("Job with name " + self._job_name + " already exists")

        # create job from file
        if file_name:
            if os.path.isabs(file_name):
                self._file_name = file_name
            else:
                self._file_name = self._workspace._working_directory + os.sep + file_name
            # check if file does exist
            if not os.path.isfile(self._file_name):
                self._file_name = self._file_name + ".gms"
            if not os.path.isfile(self._file_name):
                raise gams.control.workspace.GamsException(f"Could not create GamsJob instance from non-existing file {self._file_name}")

        # create job from source
        elif source:
            self._file_name = self._workspace._working_directory + os.sep + self._job_name + ".gms"
            with open(self._file_name, "w") as file:
                file.write(source)

    def __del__(self):
        self._workspace._debug_out("---- Entering GamsJob destructor ----", 0)

    def _remove_tmp_cp(self, tmp_cp, checkpoint):
        if tmp_cp:
            try:
                os.remove(os.path.join(self._workspace._working_directory, checkpoint._checkpoint_file_name))
            except (FileNotFoundError, PermissionError):
                pass
            shutil.move(tmp_cp._checkpoint_file_name, checkpoint._checkpoint_file_name)

    def _remove_tmp_opt(self, tmp_opt, pf_file_name):
        del tmp_opt
        if self._workspace._debug < gams.control.workspace.DebugLevel.KeepFiles:
            try:
                os.remove(pf_file_name)
            except (FileNotFoundError, PermissionError):
                pass

    def _prepare_run(self, gams_options=None, checkpoint=None, output=None, create_out_db=True, databases=None, relative_paths=False):
        tmp_cp = None
        tmp_opt = GamsOptions(self._workspace, gams_options)

        if self._checkpoint_start:
            if relative_paths:
                tmp_opt._restart = os.path.relpath(
                    self._checkpoint_start._checkpoint_file_name, self._workspace._working_directory)
            else:
                tmp_opt._restart = self._checkpoint_start._checkpoint_file_name
        if checkpoint:
            if self._checkpoint_start == checkpoint:
                tmp_cp = GamsCheckpoint(self._workspace)
                if relative_paths:
                    tmp_opt._save = os.path.relpath(
                        tmp_cp.name, self._workspace._working_directory)
                else:
                    tmp_opt._save = tmp_cp.name
            else:
                if relative_paths:
                    tmp_opt._save = os.path.relpath(
                        checkpoint._checkpoint_file_name, self._workspace._working_directory)
                else:
                    tmp_opt._save = checkpoint._checkpoint_file_name

        # implement log_option member in GamsOptions class
        if self._workspace._debug >= gams.control.workspace.DebugLevel.ShowLog:
            optSetIntStr(tmp_opt._opt, "LogOption", 4)
        elif optGetIntStr(tmp_opt._opt, "LogOption") != 2:
            if not output:
                optSetIntStr(tmp_opt._opt, "LogOption", 0)
            else:
                optSetIntStr(tmp_opt._opt, "LogOption", 4)

        # handle s single database and a collection of databases
        db_paths = set()
        if databases:
            if isinstance(databases, GamsDatabase):
                databases = [databases]
            for db in databases:
                db_paths.add(os.path.join(
                    self._workspace._working_directory, db._database_name + ".gdx"))
                db.export()
                if db._in_model_name:
                    tmp_opt.defines[db._in_model_name] = db.name

        if len(tmp_opt.defines) > 0:
            save_eol_only = optEOLOnlySet(tmp_opt._opt, 0)
            gms_param = ""
            for k, v in iter(tmp_opt.defines.items()):
                gms_param = "--" + k + "=" + v
                optReadFromStr(tmp_opt._opt, gms_param)
            optEOLOnlySet(tmp_opt._opt, save_eol_only)

        if len(tmp_opt.idir) > 0:
            if len(tmp_opt.idir) > 40:
                raise gams.control.workspace.GamsException(
                    "Cannot handle more than 40 IDirs", self._workspace)

            for i in range(len(tmp_opt.idir)):
                optSetStrStr(tmp_opt._opt, "InputDir" +
                             str(i + 1), tmp_opt.idir[i])

        for i in range(1, gmoProc_nrofmodeltypes):
            optSetStrStr(tmp_opt._opt, cfgModelTypeName(
                tmp_opt._cfg, i), tmp_opt._selected_solvers[i])
        if create_out_db:
            if tmp_opt.gdx == "":
                tmp_opt.gdx = self._workspace._database_add()

        if len(tmp_opt._logfile) == 0:
            if relative_paths:
                tmp_opt._logfile = self._job_name + ".log"
            else:
                tmp_opt._logfile = self._workspace._working_directory + \
                    os.sep + self._job_name + ".log"

        if not gams_options or not gams_options.output:
            tmp_opt.output = self._job_name + ".lst"

        if relative_paths:
            tmp_opt._input = os.path.relpath(
                self._file_name, self._workspace._working_directory)
        else:
            tmp_opt._curdir = self._workspace._working_directory
            tmp_opt._input = self._file_name

        pf_file_name = self._workspace._working_directory + os.sep + self._job_name + ".pf"
        if optWriteParameterFile(tmp_opt._opt, pf_file_name) != 0:
            raise gams.control.workspace.GamsException(
                "Could not write parameter file " + pf_file_name + " for GamsJob " + self._job_name, self._workspace)

        return tmp_cp, tmp_opt, pf_file_name, db_paths

    def run(self, gams_options=None, checkpoint=None, output=None, create_out_db=True, databases=None):
        '''
        @brief Run GamsJob
        @param gams_options GAMS options to control job
        @param checkpoint GamsCheckpoint to be created by GamsJob
        @param output Stream to capture GAMS log (e.g. sys.stdout or an object created by the build-in function open())
        @param create_out_db Flag to define if out_db should be created
        @param databases Either a GamsDatabase or a list of GamsDatabases to be read by the GamsJob
        '''

        tmp_cp, tmp_opt, pf_file_name, _ = self._prepare_run(
            gams_options, checkpoint, output, create_out_db, databases)

        capture_output = self._workspace._debug >= gams.control.workspace.DebugLevel.ShowLog or output
        stdout_val = None
        if capture_output:
            stdout_val = subprocess.PIPE

        #TODO: Popen will throw an exception. should we capture it and throw a new exception from GAMS api
        #redirect output like in C#!
        if gams.control.workspace._is_win:
            si = subprocess.STARTUPINFO()
            try:
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
            except:
                si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess._subprocess.SW_HIDE
            self._p = subprocess.Popen(self._workspace._system_directory + os.sep + "gams.exe dummy pf=" + self._job_name + ".pf", stdout=stdout_val, cwd=self._workspace._working_directory, startupinfo=si, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            self._p = subprocess.Popen([self._workspace._system_directory + os.sep + "gams", "dummy", "pf=" + self._job_name + ".pf"], stdout=stdout_val, cwd=self._workspace._working_directory)

        if capture_output:
            write_buffer = hasattr(output, "buffer") and sys.platform == "win32"
            stdout_reader = io.TextIOWrapper(self._p.stdout, newline="")
            while True:
                try:
                    data = stdout_reader.readline()
                except:
                    pass
                if data == "" and self._p.poll() != None:
                    break
                if self._workspace._debug >= gams.control.workspace.DebugLevel.ShowLog:
                    print(data, end="", flush=True)
                else:
                    if write_buffer:
                        output.buffer.write(data.encode())  # write directly to the buffer if possible to avoid extra new lines e.g. for files opened without newline='' on Windows
                    else:
                        output.write(data)
                    output.flush()

        exitcode = self._p.wait()

        if create_out_db == True:
            gdx_path = os.path.splitext(tmp_opt.gdx)[0]
            gdx_path = gdx_path + ".gdx"
            if not os.path.isabs(gdx_path):
                gdx_path = os.path.join(self._workspace._working_directory, gdx_path)
            if os.path.isfile(gdx_path):
                self._out_db = GamsDatabase(self._workspace, database_name=os.path.splitext(os.path.basename(gdx_path))[0] , gdx_file_name=gdx_path,  force_name=True)

        if  exitcode != 0:
            if self._workspace._debug < gams.control.workspace.DebugLevel.KeepFilesOnError and self._workspace._using_tmp_working_dir:
                raise gams.control.workspace.GamsExceptionExecution("GAMS return code not 0 (" + str(exitcode) + "), set the debug flag of the GamsWorkspace constructor to DebugLevel.KeepFilesOnError or higher or define a working_directory to receive a listing file with more details", exitcode, self._workspace)
            else:
                raise gams.control.workspace.GamsExceptionExecution("GAMS return code not 0 (" + str(exitcode) + "), check " + self._workspace._working_directory + os.path.sep + tmp_opt.output + " for more details", exitcode, self._workspace)
        self._p = None

        self._remove_tmp_cp(tmp_cp, checkpoint)
        self._remove_tmp_opt(tmp_opt, pf_file_name)

    def run_engine(self, engine_configuration, extra_model_files=None, engine_options=None, gams_options=None,
                   checkpoint=None, output=None, create_out_db=True, databases=None, remove_results=True):
        '''
        @brief Run GamsJob on GAMS Engine
        @param engine_configuration GamsEngineConfiguration object
        @param extra_model_files List of additional file paths (apart from main file) required to run the model (e.g. include files)
        @param engine_options Dictionary of GAMS Engine options to control job execution
        @param gams_options GAMS options to control job
        @param checkpoint GamsCheckpoint to be created by GamsJob
        @param output Stream to capture GAMS log (e.g. sys.stdout or an object created by the build-in function open())
        @param create_out_db Flag to define if out_db should be created
        @param databases Either a GamsDatabase or a list of GamsDatabases to be read by the GamsJob
        @param remove_results Remove results from GAMS Engine after downloading them
        '''

        import urllib3
        import certifi

        if not isinstance(engine_configuration, GamsEngineConfiguration):
            raise gams.control.workspace.GamsException(
                "engine_configuration is not a valid GamsEngineConfiguration instance", self._workspace)

        request_headers = {"Authorization": engine_configuration._get_auth_header(),
                          "User-Agent": "GAMS Python API",
                          "Accept": "application/json"}

        def remove_job_results():
            if remove_results is not True:
                return
            for attempt_number in range(self._max_request_attempts):
                r = self._http.request(
                    "DELETE",
                    engine_configuration.host + "/jobs/" + self._p._token + "/result",
                    headers=request_headers
                )
                response_data = r.data.decode("utf-8", errors="replace")
                if r.status in [200, 403]:
                    return
                elif r.status == 429:
                    # retry
                    time.sleep(2**attempt_number)
                    continue
                raise gams.control.workspace.GamsException(
                    "Removing job result failed with status code: " + str(r.status) + ". Message: " + response_data, self._workspace)
            else:
                raise gams.control.workspace.GamsException(
                    "Removing job result failed after: " + str(self._max_request_attempts) + " attempts. Message: " + response_data, self._workspace)

        if int(urllib3.__version__.split('.')[0]) >= 2:  # urllib3 uses TLS 1.2 as minimum version per default beginning with version 2.0
            self._http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        else:  # enforce TLS 1.2 as minimum version for urllib<2.0
            import ssl
            self._http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where(), ssl_minimum_version=ssl.TLSVersion.TLSv1_2)

        tmp_cp, tmp_opt, pf_file_name, db_paths = self._prepare_run(
            gams_options, checkpoint, output, create_out_db, databases, relative_paths=True)

        capture_output = self._workspace._debug >= gams.control.workspace.DebugLevel.ShowLog or output

        model_data_zip = io.BytesIO()

        main_file_name = self._file_name
        model_files = {main_file_name, pf_file_name}
        model_files.update(db_paths)

        if self._checkpoint_start:
            model_files.add(self._checkpoint_start._checkpoint_file_name)

        if extra_model_files:
            if not isinstance(extra_model_files, list):
                extra_model_files = [extra_model_files]
            extra_model_files_cleaned = {x if os.path.isabs(x) else os.path.join(
                self._workspace._working_directory, x) for x in extra_model_files}
            model_files.update(extra_model_files_cleaned)

        with zipfile.ZipFile(model_data_zip, 'w', zipfile.ZIP_DEFLATED) as model_data:
            for model_file in model_files:
                model_data.write(model_file, arcname=os.path.relpath(
                    model_file, self._workspace._working_directory) if os.path.isabs(model_file) else model_file)

        model_data_zip.seek(0)

        file_params = {}

        query_params = copy.deepcopy(engine_options) if engine_options else {}

        query_params["namespace"] = engine_configuration.namespace

        if "data" in query_params or "model_data" in query_params:
            raise gams.control.workspace.GamsException(
                "`engine_options` must not include keys `data` or `model_data` . Please use `extra_model_files` to provide additional files to send to GAMS Engine.", self._workspace)

        if "inex_file" in query_params:
            if isinstance(query_params["inex_file"], io.IOBase):
                file_params["inex_file"] = ("inex.json", query_params["inex_file"].read(), "application/json")
            else:
                with open(query_params["inex_file"], "rb") as f:
                    file_params["inex_file"] = ("inex.json", f.read(), "application/json")
            del query_params["inex_file"]

        if "model" in query_params:
            file_params["data"] = (
                "data.zip", model_data_zip.read(), "application/zip")
        else:
            query_params["run"] = tmp_opt._input
            query_params["model"] = os.path.splitext(tmp_opt._input)[0]
            file_params["model_data"] = (
                "data.zip", model_data_zip.read(), "application/zip")

        model_data_zip.close()

        if "arguments" in query_params:
            if not isinstance(query_params["arguments"], list):
                query_params["arguments"] = [query_params["arguments"]]
            query_params["arguments"].append("pf=" + self._job_name + ".pf")
        else:
            query_params["arguments"] = ["pf=" + self._job_name + ".pf"]

        for attempt_number in range(self._max_request_attempts):
            r = self._http.request(
                "POST",
                engine_configuration.host + "/jobs/?" +
                urllib.parse.urlencode(query_params, doseq=True),
                fields=file_params,
                headers=request_headers
            )
            response_data = r.data.decode("utf-8", errors="replace")
            if r.status == 201:
                break
            elif r.status == 429:
                # retry
                time.sleep(2**attempt_number)
                continue
            raise gams.control.workspace.GamsException(
                "Creating job on GAMS Engine failed with status code: " + str(r.status) + ". Message: " + response_data, self._workspace)
        else:
            raise gams.control.workspace.GamsException(
                "Creating job on GAMS Engine failed after: " + str(self._max_request_attempts) + " attempts. Message: " + response_data, self._workspace)


        self._p = GamsEngineJob(json.loads(response_data)[
            "token"], engine_configuration, request_headers)
        
        poll_logs_sleep_time = 1

        while True:
            r = self._http.request(
                "DELETE",
                engine_configuration.host + "/jobs/" + self._p._token + "/unread-logs",
                headers=request_headers
            )
            response_data = r.data.decode("utf-8", errors="replace")
            if r.status == 429:
                # too many requests, slow down
                poll_logs_sleep_time = min(poll_logs_sleep_time + 1, 5)
                time.sleep(poll_logs_sleep_time)
                continue
            elif r.status == 403:
                # job still in queue
                time.sleep(poll_logs_sleep_time)
                continue
            elif r.status != 200:
                raise gams.control.workspace.GamsException(
                    "Getting logs failed with status code: " + str(r.status) + ". Message: " + response_data, self._workspace)
            response_data = json.loads(response_data)
            if capture_output:
                stdout_data = response_data["message"]
                if self._workspace._debug >= gams.control.workspace.DebugLevel.ShowLog:
                    if stdout_data != '':
                        print(stdout_data, end="")
                    sys.stdout.flush()
                else:
                    output.write(stdout_data)
                    output.flush()
            if response_data["queue_finished"] is True:
                exitcode = response_data["gams_return_code"]
                break
            time.sleep(poll_logs_sleep_time)

        for attempt_number in range(self._max_request_attempts):
            r = self._http.request(
                "GET",
                engine_configuration.host + "/jobs/" + self._p._token + "/result",
                headers=request_headers,
                preload_content=False
            )

            if r.status == 200:
                break

            response_data = r.data.decode("utf-8", errors="replace")
            if r.status == 429:
                # retry
                time.sleep(2**attempt_number)
                continue

            raise gams.control.workspace.GamsException(
                "Downloading job result failed with status code: " + str(r.status) + ". Message: " + response_data, self._workspace)
        else:
            raise gams.control.workspace.GamsException(
                "Downloading job result failed after: " + str(self._max_request_attempts) + " attempts. Message: " + response_data, self._workspace)

        fd, path = tempfile.mkstemp()

        try:
            with open(path, 'wb') as out:
                while True:
                    data = r.read(6000)
                    if not data:
                        break
                    out.write(data)

            r.release_conn()

            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(self._workspace._working_directory)
        finally:
            os.close(fd)
            os.remove(path)

        remove_job_results()

        if create_out_db:
            gdx_path = os.path.splitext(tmp_opt.gdx)[0]
            gdx_path = gdx_path + ".gdx"
            if not os.path.isabs(gdx_path):
                gdx_path = os.path.join(
                    self._workspace._working_directory, gdx_path)
            if os.path.isfile(gdx_path):
                self._out_db = GamsDatabase(self._workspace, database_name=os.path.splitext(
                    os.path.basename(gdx_path))[0], gdx_file_name=gdx_path,  force_name=True)

        if exitcode != 0:
            if self._workspace._debug < gams.control.workspace.DebugLevel.KeepFiles and self._workspace._using_tmp_working_dir:
                raise gams.control.workspace.GamsExceptionExecution("GAMS return code not 0 (" + str(
                    exitcode) + "), set the debug flag of the GamsWorkspace constructor to DebugLevel.KeepFiles or higher or define a working_directory to receive a listing file with more details", exitcode, self._workspace)
            else:
                raise gams.control.workspace.GamsExceptionExecution("GAMS return code not 0 (" + str(
                    exitcode) + "), check " + self._workspace._working_directory + os.path.sep + tmp_opt.output + " for more details", exitcode, self._workspace)
        self._p = None

        self._remove_tmp_cp(tmp_cp, checkpoint)
        self._remove_tmp_opt(tmp_opt, pf_file_name)

    def interrupt(self):
        '''
        @brief Send Interrupt to running Job. Note: On Mac OS this call requires the tool pstree to be installed
        @return False if no process available, True otherwise
        '''
        
        if self._p != None:
            if isinstance(self._p, GamsEngineJob):
                for attempt_number in range(self._max_request_attempts):
                    r = self._http.request(
                        "DELETE",
                        self._p._configuration.host + "/jobs/" + self._p._token + "?hard_kill=false",
                        headers=self._p._request_headers
                    )
                    response_data = r.data.decode("utf-8", errors="replace")
                    if r.status in [200, 400]:
                        return True
                    elif r.status == 429:
                        # retry
                        time.sleep(2**attempt_number)
                        continue
                    raise gams.control.workspace.GamsException(
                        "Interrupting Engine job failed with status code: " + str(r.status) + ". Message: " + response_data)
                else:
                    raise gams.control.workspace.GamsException(
                        "Interrupting Engine job failed after: " + str(self._max_request_attempts) + " attempts. Message: " + response_data)

            if gams.control.workspace._is_win:
                import ctypes

                class _CopyDataStruct(ctypes.Structure):
                    ## @cond DOXYGEN_IGNORE_THIS
                    _fields_ = [('dwData', ctypes.c_char_p),
                                ('cbData', ctypes.c_ulong),
                                ('lpData', ctypes.c_char_p)]
                    ## @endcond

                if sys.version_info[0] >= 3:
                    wid = bytes("___GAMSMSGWINDOW___" + str(self._p.pid), 'utf-8')
                    receiver = ctypes.windll.user32.FindWindowA(None, wid)
                    cmd = bytes("GAMS Message Interrupt", 'utf-8')
                else:
                    receiver = ctypes.windll.user32.FindWindowA(None, "___GAMSMSGWINDOW___" + str(self._p.pid))
                    cmd = "GAMS Message Interrupt"

                cs = _CopyDataStruct()

                cs.dwData = 1
                cs.cbData = len(cmd) + 1
                cs.lpData = cmd

                WM_COPYDATA = 0x4A
                ctypes.windll.user32.SendMessageA(receiver, WM_COPYDATA, 0, ctypes.byref(cs))
                return True
            else:
                proc = subprocess.Popen(["/bin/bash","-c", "kill -2 " + str(self._p.pid)], stdout=subprocess.PIPE, cwd=self._workspace._working_directory)
        else:
            return False


