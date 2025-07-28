"""
Safelib is a library that provides safe import mechanisms for Python modules.

Example usage:
```python
import safelib

from safelib import Import
with Import('typing', 'typing_extensions') as importer:
    from safelib import Protocol # use traditional import
    final = importer.final # use importer to access the final
```

For inquiries, please contact the author at contact@tomris.dev
"""

import importlib
from types import ModuleType
from typing import Any, Optional, Protocol, TypeAlias, Union

Module: TypeAlias = str
Entity: TypeAlias = Union[Any, type, object]
SafeEntity: TypeAlias = Union[ModuleType, Entity, "_Sentinel", "_Future", type['NotFound']]

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
        _sentinel = _Sentinel()
        _sentinel.value = self.value
        _sentinel.empty = self.empty
        _sentinel.future = self.future
        return _sentinel

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

    _raise_exc: bool = False
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
        self._raise_exc

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

    def __init__(self, main: str, fallback: str, raises: bool = True, search_builtins: bool = False):
        self.main = main
        self.fallback = fallback
        self._search_builtins = search_builtins
        self._old_state = None
        if not raises: state.catch()

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

    def enter(self) -> 'Import':
        self._old_state = _State()
        self._old_state.main = state.main.copy()
        self._old_state.fallback = state.fallback.copy()

        state._search_builtins = self._search_builtins

        state.main.value = self.main
        state.main.empty = False
        state.main.future = False

        state.fallback.value = self.fallback
        state.fallback.empty = False
        state.fallback.future = False

        return self

    def exit(self, exc_type, exc_val, exc_tb):
        state.main = self._old_state.main.copy()
        state.fallback = self._old_state.fallback.copy()
        state._raise_exc = self._old_state._raise_exc
        state._search_builtins = self._old_state._search_builtins

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

    def __enter__(self) -> 'Import':
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> 'Import':
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
        val = getattr(importlib.import_module('builtins'), name, NotFound)
        if val is not NotFound:
            state.add_name(name, 'builtins', val)
            return val
    if origin is None:
        value = importlib.import_module(name)
    elif default is not None:
        value = getattr(importlib.import_module(origin), name, default)
    else:
        value = getattr(importlib.import_module(origin), name)
    state.add_name(name, origin, value)
    return value

def __getattr__(name: str, state: _State | None = None) -> SafeEntity:
    """
    Dynamic attribute access for the safelib module.

    Args:
        name (str): The name of the attribute to access.
        state (_State): State manager instance.

    Returns:
        typing.Any: The value of the attribute.
    """
    if state is None:
        state = _State()

    if name == "_reset":
        state.reset()

    elif name == "_main":
        state.main.value = _Future
        state.main.empty = False
        state.main.future = True
        return state.main

    elif name == "_fallback":
        state.fallback.value = _Future
        state.fallback.empty = False
        state.fallback.future = True
        return state.fallback
    else:

        if state.main.future:
            state.main.value = name
            state.main.future = False
            print(f"Setting state.main to {name}")

        if state.fallback.future:
            state.fallback.value = name
            state.fallback.future = False
            print(f"Setting state.fallback to {name}")

        if state.main.value:
            try:
                if name == state.main.value:
                    return import_name(name)
                return import_name(name, state.main.value)
            except (ImportError, AttributeError, ModuleNotFoundError):
                if not state.fallback.empty:
                    if name == state.fallback.value:
                        try:
                            return import_name(name)
                        except ImportError:
                            if state.raises:
                                raise ImportError(
                                    f"Module '{state.fallback.value}' not found"
                                )
                            else:
                                return NotFound
                    if state.raises:
                        return import_name(name, state.fallback.value)
                    else:
                        return import_name(name, state.fallback.value, default=NotFound)
                if state.raises:
                    raise ImportError(
                        f"Module '{state.main.value}' has no attribute '{name}'"
                    )
                else:
                    return NotFound
        return NotFound
