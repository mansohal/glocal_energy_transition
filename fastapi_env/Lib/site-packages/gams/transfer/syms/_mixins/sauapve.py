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

import weakref
import gams.transfer._abcs as abcs
from gams.transfer._internals import CasePreservingDict, GAMS_SYMBOL_MAX_LENGTH


class SAUAPVEMixin:
    @property
    def modified(self):
        """
        Flag that identifies if the symbol has been modified
        """
        return self._modified

    @modified.setter
    def modified(self, modified):
        if not isinstance(modified, bool):
            raise TypeError("Attribute 'modified' must be type bool")

        self._modified = modified

    @property
    def container(self):
        """Container of the symbol"""
        return self._container

    @container.setter
    def container(self, container):
        if not isinstance(container, abcs.ABCContainer):
            raise TypeError("Symbol 'container' must be type Container")

        # create a weak proxy to help garbage collection
        container = weakref.proxy(container)

        # if old_container != new_container
        if getattr(self, "container", None) is not None:
            if self.container != container:
                # reset check flags for old container
                self.container._requires_state_check = True
                self.container.modified = True

        # set new container
        self._container = container

        # set check flags for new container
        self.container._requires_state_check = True
        self.container.modified = True

        # set check flags for symbol
        self._requires_state_check = True
        self.modified = True

    def isValid(self, verbose: bool = False, force: bool = False) -> bool:
        """
        Checks if the symbol is in a valid format

        Parameters
        ----------
        verbose : bool, optional
            Throw exceptions if verbose=True, by default False
        force : bool, optional
            Recheck a symbol if force=True, by default False

        Returns
        -------
        bool
            True if a symbol is in valid format, False otherwise (throws exceptions if verbose=True)
        """
        if not isinstance(verbose, bool):
            raise ValueError("Argument 'verbose' must be type bool")

        if not isinstance(force, bool):
            raise ValueError("Argument 'force' must be type bool")

        if force:
            self._requires_state_check = True

        if self._requires_state_check:
            try:
                self._assert_is_valid()
                return True
            except Exception as err:
                if verbose:
                    raise err
                return False
        else:
            return True

    @property
    def name(self):
        """
        Name of symbol
        """
        return self._name

    @name.setter
    def name(self, name):
        if not isinstance(name, str):
            raise TypeError("Symbol 'name' must be type str")

        if not len(name) <= GAMS_SYMBOL_MAX_LENGTH:
            raise ValueError(
                "GAMS symbol 'name' is too long, "
                f"max is {GAMS_SYMBOL_MAX_LENGTH} characters"
            )

        if name[0] == "_":
            raise Exception("Valid GAMS names cannot begin with a '_' character.")

        if not all(True if i == "_" else i.isalnum() for i in name):
            raise Exception(
                "Detected an invalid GAMS symbol name. "
                "GAMS names can only contain alphanumeric characters "
                "(letters and numbers) and the '_' character."
            )

        if getattr(self, "name", None) is not None:
            # special case when wanting to change the casing of a symbol name
            if self.name.casefold() == name.casefold():
                self._requires_state_check = True

                self.container.data = CasePreservingDict(
                    {
                        name if k.casefold() == self.name.casefold() else k: v
                        for k, v in self.container
                    }
                )

                self.container._requires_state_check = True
                self.container.modified = True

                # set the name
                self._name = name
                self.modified = True

            elif self.name != name:
                self._requires_state_check = True

                if name in self.container:
                    raise Exception(
                        f"Attempting rename symbol `{self.name}` to `{name}` "
                        "but a symbol with this name already exists in the Container. "
                        "All symbols in a single Container instance must have unique names. "
                        "The user can remedy this issue by "
                        "1) removing the original symbol from the Container with the removeSymbols() method, or "
                        "2) creating separate Container instances. "
                    )

                self.container.data = CasePreservingDict(
                    {name if k == self.name else k: v for k, v in self.container}
                )
                self.container._requires_state_check = True
                self.container.modified = True

                # set the name
                self._name = name
                self.modified = True

                # update any records column headings
                for symname, symobj in self.container:
                    if symobj.records is not None and name in symobj.domain_names:
                        symobj.modified = True

        else:
            if name in self.container:
                raise ValueError(
                    f"Attempting to add a symbol named `{name}` "
                    "but one already exists in the Container. "
                    "Symbol replacement is only possible if the symbol is "
                    "first removed from the Container with the removeSymbols() method."
                )

            # set the name
            self._name = name
            self.modified = True
