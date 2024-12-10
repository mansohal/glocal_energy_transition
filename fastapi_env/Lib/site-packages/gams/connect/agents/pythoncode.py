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

from gams.connect.agents.connectagent import ConnectAgent


class PythonCode(ConnectAgent):

    def __init__(self, cdb, inst):
        super().__init__(cdb, inst)
        inst = self._normalize_instructions(inst)
        self._parse_options(inst)
        if self._trace > 0:
            self._log_instructions(inst)

    def __del__(self):
        pass

    def _parse_options(self, inst):
        self._code = inst["code"]
        self._trace = inst["trace"]

    def execute(self):
        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (before):")

        loc = dict(locals())
        loc["instructions"] = []
        loc["connect"] = self._cdb
        loc["gams"] = self._cdb.ecdb
        exec(self._inst["code"], loc)

        if self._trace > 1:
            self._cdb.print_log(
                f"Number of generated instructions: {len(loc['instructions'])}"
            )
        if self._trace > 2:
            self._cdb.print_log("List of generated instructions:")
            for idx, gen_inst in enumerate(loc["instructions"]):
                if isinstance(gen_inst, dict):
                    agent_name = list(gen_inst.keys())[0]
                    self._log_instructions(
                        gen_inst[agent_name], description=f"({idx + 1}) {agent_name}:"
                    )
                else:
                    self._cdb.print_log(
                        f"Warning: Could not log generated instructions since item {idx} was not of type 'dict' but '{type(gen_inst).__name__}'."
                    )
            self._cdb.print_log("")

        if self._trace > 0:
            self._describe_container(self._cdb.container, "Connect Container (after):")

        return loc["instructions"]
