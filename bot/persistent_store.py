"""
hunter-bot - A discord bot for hunter written in pycord
Copyright (C) 2024  BobDotCom

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import pickle
from collections.abc import Container
from os import PathLike
from typing import Any


class PersistentStore:
    __slots__ = ("_path", "_data", "_keys")

    def __init__(
            self,
            path: int | str | bytes | PathLike[str] | PathLike[bytes],
            keys: Container[str] = None,  # TODO: better typing
    ):
        """
        A persistent storage that stores normal python objects. Upon shutdown, it will pickle the data and save it to a
        storage file. Upon initialization, it will attempt to load the data if possible.

        :param path: The path of the storage file.
        :param keys: A list of permitted keys. If not provided, it will allow all keys. Additionally, if provided it
        will set a default value of None to all unset keys upon initialization.
        """
        self._path = path
        self._keys = keys
        self._data: dict[str, Any] = {}
        if os.path.exists(self._path):
            with open(self._path, "rb") as f:
                self._data = pickle.load(f)
                self._validate_keys()
        if keys is not None:
            for key in keys:
                self._data.setdefault(key)

    def __setattr__(self, key: Any, value: Any) -> None:
        if key in self.__slots__:
            super().__setattr__(key, value)
        else:
            self._validate_key(key)
            self._data[key] = value

    def __getattr__(self, key: Any) -> Any:
        return self._data[key]

    def __delattr__(self, key: Any) -> None:
        del self._data[key]

    def _validate_key(self, key: str):
        if self._keys is None:
            return True

        if key not in self._keys:
            raise KeyError(
                f'Key "{key}" is not permitted. Allowed keys are: {self._keys}'
            )

    def _validate_keys(self):
        for key in self._data:
            self._validate_key(key)

    # def setdefault(self, key: str, default: Any = None) -> Any:
    #     """
    #     Invokes dict.setdefault on the internal data storage and returns the result.
    #     See https://docs.python.org/3.12/library/stdtypes.html#dict.setdefault.
    #     """
    #     return self._data.setdefault(key, default)

    def save(self):
        with open(self._path, "wb") as f:
            pickle.dump(self._data, f)
