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

import importlib
import sys
from gams.connect.agents.connectagent import ConnectAgent
from gams.connect.connectvalidator import ConnectValidator
from gams.connect.errors import GamsConnectException
from gams.control import GamsWorkspace
from gams.transfer import Container


class ConnectDatabase(object):
    """
    A ConnectDatabase contains data in the form of a gams.transfer.Container instance.
    Running the execute() method instantiates Connect agents that read, write, or modify
    symbol data.

    Parameters
    ----------
    system_directory : str
        GAMS system directory to be used.
    container : gams.transfer.Container, optional
        A Container to be used by the ConnectDatabase, by default None. If omitted, the ConnectDatabase will instantiate a new and empty container.
    ecdb : gams.core.embedded.ECGAMSDatabase, optional
        When running in a GAMS context (e.g. embedded code), this can be used to allow connection to the embedded code GAMS database, by default None.
    """

    def __init__(self, system_directory, container=None, ecdb=None):
        self._system_directory = system_directory
        self._ecdb = ecdb
        self._ws = GamsWorkspace(system_directory=self._system_directory)
        if container is None:
            self._container = Container(system_directory=self._system_directory)
        else:
            self._container = container
        if self._ecdb:
            ecdb._cdb = self

    def __del__(self):
        pass

    def print_log(self, msg, end="\n"):
        """
        Print msg to the GAMS log if avaiable, uses print() otherwise.

        Parameters
        ----------
        msg : str
            The message to be printed.
        end : str, optional
            String to be put after the message, by default "\n".
        """
        if self._ecdb:
            self._ecdb.printLog(msg, end)
        else:
            print(msg, end=end)
            sys.stdout.flush()

    def _get_agent_class(self, agent_name):
        try:
            mod = importlib.import_module("gams.connect.agents." + agent_name.lower())
        except ModuleNotFoundError as e:
            if (
                e.name != "gams.connect.agents." + agent_name.lower()
            ):  # the connect agent module itself was found but an import in the source itself did fail
                raise GamsConnectException(str(e), traceback=True)
            mod = importlib.import_module(agent_name.lower())
        agent_class = vars(mod)[agent_name]
        return agent_class

    def execute(self, instructions):
        """
        Instantiates and executes one or multiple Connect agents.

        Parameters
        ----------
        instructions : list, dict
            The instructions to be used for instantiating and executing the agents. Use list for executnig multiple agents and dict for a single one.

        Raises
        ----------
        GamsConnectException
            If the instructions are invalid or if the specified agent could not be loaded.
        """
        if isinstance(instructions, list):
            if all(isinstance(inst, dict) for inst in instructions):
                inst_list = instructions
            else:
                raise GamsConnectException(
                    "Invalid data type for instructions argument. Needs to be 'list of dict'."
                )
        elif isinstance(instructions, dict):
            inst_list = [instructions]
        else:
            raise GamsConnectException(
                f"Invalid data type for instructions argument. Needs to be 'dict' or 'list', but was '{type(instructions).__name__}'."
            )

        for inst in inst_list:
            root = list(inst.keys())
            if len(root) != 1:
                raise GamsConnectException(
                    f"Invalid agent definition with {len(root)} agent names instead of 1."
                )
            agent_name = root[0]
            if not isinstance(agent_name, str):
                raise GamsConnectException(
                    f"Invalid data type for agent name. Needs to be 'str', but was '{type(agent_name).__name__}'."
                )

            inst = inst[agent_name]
            agent_class = self._get_agent_class(agent_name)
            agent_schema = agent_class.cerberus()
            v = ConnectValidator(agent_schema)
            if not v.validate(inst):
                raise GamsConnectException(
                    f"Validation of input for agent '{agent_name}' failed: {v.errors}"
                )
            if not issubclass(agent_class, ConnectAgent):
                raise GamsConnectException(
                    f"Agent class '{agent_name}' has to be derived from gams.connect.agents.connectagent.ConnectAgent",
                    traceback=True,
                )
            agent_instance = agent_class(self, inst)
            agent_instance.open()
            execute_return = agent_instance.execute()
            agent_instance.close()
            if (
                agent_name == "PythonCode" and execute_return
            ):  # PythonCode generated instructions
                self.execute(execute_return)

    @property
    def container(self):
        return self._container

    @property
    def ecdb(self):
        return self._ecdb

    @property
    def system_directory(self):
        return self._system_directory
