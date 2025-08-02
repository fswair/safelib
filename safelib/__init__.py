"""
Safelib is a library that provides safe importing mechanisms for Python modules.

You can easily integrate complex import logic into your codebase without worrying about
import errors or namespace conflicts. Safelib allows you to import modules and entities
safely, with options to handle exceptions gracefully or search built-in modules.

Example usage:
```python
import safelib

from safelib import Import
with Import('sqlalchemy', 'peewee', raises=False, search_builtins=True) as orm:
    from safelib import declarative_base # use traditional import
    Base = orm.declarative_base # use orm to access the declarative_base

    # declarative_base can be found entity or safelib.NotFound
    # because we set raises=False, it will not raise an exception if the entity is not found

    # when we search for `int` with orm.int, it will search first in the builtins module
    # and return the int type if found, or safelib.NotFound if not found.

    # to validate whether an entity is valid, use:
    if safelib.valid(orm.entity):
        do_something_with(orm.entity)
```

For inquiries, please contact the author at contact@tomris.dev
"""

import importlib
import sys
from types import ModuleType
from typing import Any, Optional, Protocol, TypeAlias, Union

from .errors import EntityNotFound, NamespaceNotFound

Module: TypeAlias = str
Entity: TypeAlias = Union[Any, type, object]
SafeEntity: TypeAlias = Union[
    ModuleType, Entity, "_Sentinel", "_Future", type["NotFound"]
]


class _Sentinel:
    """
    A sentinel class that manages whether a value has been set.
    """

    value: Optional[Module] = None
    empty: bool = True
    future: bool = False

    def copy(self) -> "_Sentinel":
        """
        Create a copy of the sentinel.

        Returns:
            _Sentinel: A new instance of the sentinel with the same state.
        """
        copy_sentinel = _Sentinel()
        copy_sentinel.value = self.value
        copy_sentinel.empty = self.empty
        copy_sentinel.future = self.future
        return copy_sentinel

    def reset(self) -> None:
        """
        Reset the sentinel to its initial state.
        """
        self.value = None
        self.empty = True
        self.future = False


class _State:
    """
    A state manager class that holds the main and fallback sentinels during their lifecycle.
    """

    main: _Sentinel = _Sentinel()
    fallback: _Sentinel = _Sentinel()

    _raise_exc: bool = True
    _search_builtins: bool = False

    _imported_names: dict[str, tuple[str, SafeEntity]] = {}

    def reset(self) -> None:
        """
        Reset the state of the main and fallback sentinels.
        """
        self.main.reset()
        self.fallback.reset()

    def catch(self) -> None:
        """
        Disable raising exceptions for the current state by catching them.
        """
        self._raise_exc = False

    def raise_exc(self) -> None:
        """
        Enable raising exceptions for the current state.
        """
        self._raise_exc = True

    @property
    def raises(self) -> bool:
        """
        Get whether exceptions will catch or fall through.
        """
        return self._raise_exc

    @property
    def names(self) -> dict[str, tuple[str, SafeEntity]]:
        """
        Get the dictionary of imported names.

        Returns:
            dict: The dictionary of imported names.
        """
        return self._imported_names

    def add_name(self, name: str, origin: str, value: SafeEntity) -> None:
        """
        Add a name to the imported names dictionary.
        """
        self._imported_names[name] = (origin, value)


class _Future(Protocol):
    """
    A sentinel class to represent a future value that has not yet been set.
    """

    pass


class NotFound(Protocol):
    """
    A sentinel class to represent a value that has not been found in the import context.
    """

    pass


state = _State()


class Import:
    """
    Context manager for scoped safe imports.
    """

    def __init__(
        self,
        main: str,
        fallback: str,
        raises: bool = True,
        search_builtins: bool = False,
    ):
        self.main = main
        self.fallback = fallback
        self._search_builtins = search_builtins
        self._old_state = None
        self._raises = raises

    @staticmethod
    def valid(entity: SafeEntity) -> bool:
        """
        Check if the entity is valid within the current import context.

        Args:
            entity (SafeEntity): The entity to check.

        Returns:
            bool: True if the entity is valid, False otherwise.
        """
        return entity is not NotFound

    def enter(self) -> "Import":
        self._old_state = _State()
        self._old_state.main = state.main.copy()
        self._old_state.fallback = state.fallback.copy()

        state._search_builtins = self._search_builtins
        state._raise_exc = self._raises

        state.main.value = self.main
        state.main.empty = False
        state.main.future = False

        state.fallback.value = self.fallback
        state.fallback.empty = False
        state.fallback.future = False

        return self

    def exit(self, *args, **kwargs) -> None:
        state.main = self._old_state.main.copy()
        state.fallback = self._old_state.fallback.copy()
        state._raise_exc = self._old_state._raise_exc
        state._search_builtins = self._old_state._search_builtins

    @property
    def exc_info(self):
        """
        Get the current exception information.

        Returns:
            tuple: Exception information tuple (type, value, traceback).
        """
        return sys.exc_info()

    @property
    def exception(self) -> BaseException:
        """
        Get the current exception that occurred.

        Returns:
            BaseException: The current exception that occurred, if any.
        """
        return self.exc_info[1]

    def reset_state(self) -> None:
        """
        Reset the state of the main and fallback sentinels.
        """
        state.reset()

    def get_entity(self, name: str) -> SafeEntity:
        """
        Dynamic attribute access for the SafeImport context manager.

        Args:
            name (str): The name of the attribute to access.

        Returns:
            SafeEntity: The value of the attribute.
        """
        return __getattr__(name, state)

    def __enter__(self) -> "Import":
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> "Import":
        return self.enter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exit(exc_type, exc_val, exc_tb)

    def __getattr__(self, name: str) -> SafeEntity:
        """
        Dynamic attribute access for the SafeImport context manager.

        Args:
            name (str): The name of the attribute to access.

        Returns:
            SafeEntity: The value of the attribute.
        """
        return __getattr__(name, state)


def import_name(name: str, origin: str = None, default: Any = None) -> SafeEntity:
    if state._search_builtins:
        val = getattr(importlib.import_module("builtins"), name, NotFound)
        if val is not NotFound:
            state.add_name(name, "builtins", val)
            return val

    try:
        if origin is None:
            value = importlib.import_module(name)
        elif default is not None:
            value = getattr(importlib.import_module(origin), name, default)
        else:
            value = getattr(importlib.import_module(origin), name)

        state.add_name(name, origin or name, value)
        return value
    except (ImportError, AttributeError, ModuleNotFoundError) as e:
        if default is not None:
            return default
        raise e


def __getattr__(name: str, current_state: Optional[_State] = None) -> SafeEntity:
    """
    Dynamic attribute access for the safelib module.

    Args:
        name (str): The name of the attribute to access.
        current_state (_State): State manager instance.

    Returns:
        Any: The value of the attribute.
    """
    if current_state is None:
        current_state = state

    if name == "_reset":
        current_state.reset()
        return None

    elif name == "_no_raise":
        current_state.catch()
        return None

    elif name == "_main":
        current_state.main.empty = False
        current_state.main.future = True
        return current_state.main

    elif name == "_fallback":
        current_state.fallback.empty = False
        current_state.fallback.future = True
        return current_state.fallback
    else:
        if current_state.main.future:
            current_state.main.value = name
            current_state.main.future = False

        if current_state.fallback.future:
            current_state.fallback.value = name
            current_state.fallback.future = False

        if current_state.main.value:
            try:
                if name == current_state.main.value:
                    return import_name(name)
                return import_name(name, current_state.main.value)
            except (ImportError, AttributeError, ModuleNotFoundError):
                if not current_state.fallback.empty:
                    try:
                        if name == current_state.fallback.value:
                            return import_name(name)
                        else:
                            return import_name(name, current_state.fallback.value)
                    except (ImportError, AttributeError, ModuleNotFoundError):
                        if current_state.raises:
                            raise EntityNotFound(name, current_state.fallback.value)
                        else:
                            return NotFound

                if current_state.raises:
                    raise EntityNotFound(name, current_state.main.value)
                else:
                    return NotFound

        if current_state.raises:
            raise NamespaceNotFound(main=True)
        else:
            return NotFound


catch = state.catch
valid = Import.valid
