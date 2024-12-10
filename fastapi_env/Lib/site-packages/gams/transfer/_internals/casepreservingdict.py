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

from collections import UserDict
from typing import Any, Optional, TYPE_CHECKING
from _collections_abc import dict_items, dict_keys, dict_values


class CasePreservingDict(UserDict):
    def __init__(self, *args, **kwargs):
        self._casefolded_key_map = {}
        super().__init__(*args, **kwargs)

    def __contains__(self, key):
        return key.casefold() in self._casefolded_key_map

    def __delitem__(self, key):
        del self.data[self._casefolded_key_map[key.casefold()]]
        del self._casefolded_key_map[key.casefold()]

    def __setitem__(self, key, item):
        try:
            key_cf = key.casefold()
        except:
            raise TypeError("CasePreservingDict will only accept type str as keys")

        if key_cf not in self._casefolded_key_map:
            self.data[key] = item
            self._casefolded_key_map[key_cf] = key
        else:
            self.data[self._casefolded_key_map[key_cf]] = item

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.pretty(self.data)
        else:
            p.pretty(self.data)

    def __getitem__(self, key):
        return self.data[self._casefolded_key_map[key.casefold()]]

    def pop(self, key: str) -> Any:
        a = self.data.pop(self._casefolded_key_map[key.casefold()])
        del self._casefolded_key_map[key.casefold()]
        return a

    def get(self, key: str, value: Optional[Any] = None) -> Any:
        try:
            return self.data.get(self._casefolded_key_map[key.casefold()])
        except:
            return value

    def copy(self) -> "CasePreservingDict":
        """
        Create a deep copy of the CasePreservingDict.

        Returns
        -------
        CasePreservingDict
            A deep copy of the CasePreservingDict.
        """
        import copy

        return copy.deepcopy(self)

    def setdefault(self, key: str, default: Any) -> Any:
        """
        Set the default value for a key if it does not exist (case-insensitive).

        If the key already exists in the dictionary (case-insensitive), this function does not modify the existing value.

        Parameters
        ----------
        key : str
            The key to set the default value for.

        default : Any
            The default value to associate with the key if it does not exist.

        Returns
        -------
        Any
            The value associated with the key (case-insensitive) or the default value if the key was not found.
        """
        key_cf = key.casefold()
        if key_cf not in self._casefolded_key_map.keys():
            self.__setitem__(key, default)
            return default
        else:
            return self.data[self._casefolded_key_map[key_cf]]

    def popitem(self) -> tuple:
        return self.data.popitem()

    def items(self) -> dict_items:
        return self.data.items()

    def keys(self) -> dict_keys:
        return self.data.keys()

    def values(self) -> dict_values:
        return self.data.values()
