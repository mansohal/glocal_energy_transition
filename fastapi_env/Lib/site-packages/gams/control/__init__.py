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

import sys
is_64bits = sys.maxsize > 2**32
if not is_64bits:
    raise Exception("Python interpreter is 32 bit which is not supported by the GAMS API.")

from gams.control.workspace import *
from gams.control.database import *
from gams.control.options import *
from gams.control.execution import *

__all__ = ["DebugLevel", "GMS_MAX_INDEX_DIM", "SV_UNDEF", "SV_EPS", "GamsCheckpoint", "GamsDatabase", "GamsJob", "UpdateAction", "SymbolUpdateType", "GamsModifier", "GamsModelInstanceOpt", "GamsModelInstance", "Action", "CharSet", "GamsOptions", \
           "GamsEquationRecord", "GamsParameterRecord", "GamsSetRecord", "GamsVariableRecord", "GamsVariable", "GamsParameter", "GamsSet", "GamsEquation", "EquType", "VarType", "SetType", "SolveStat", \
           "ModelStat", "GamsWorkspace", "GamsException", "GamsExceptionExecution", "GamsExitCode", "GamsEngineConfiguration", \
           "Action", "AppendExpand", "AppendOut", "AsyncSolLst", "CaptureModelInstance", "Case", "CharSet", "CheckErrorLevel", "DFormat", "Digit", "DumpOpt", "DumpParms", "ECImplicitLoad", "Empty", "ErrMsg", "ExecMode", "FDOpt", "FileCase", "Filtered", "ForceWork", "FreeEmbeddedPython", "gdxCompress", "gdxConvert", "gdxUels", "HoldFixed", "HoldFixedAsync", "ImplicitAssign", "InteractiveSolver", "IntVarUp", "Keep", "Listing", "LogLine", "LstTitleLeftAligned", "MIIMode", "NoNewVarEqu", "On115", "PageContr", "PrefixLoadPath", "PreviousWork", "ProcTreeMemMonitor", "PutNR", "ReferenceLineNo", "Replace", "SavePoint", "ShowOSMemory", "SolPrint", "SolveLink", "SolveOpt", "StepSum", "strictSingleton", "StringChk", "SuffixDLVars", "SuffixAlgebraVars", "Suppress", "Sys10", "Sys11", "SysOut", "TFormat", "TraceOpt", "ZeroResRep" ]

