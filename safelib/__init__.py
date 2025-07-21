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

"""
Utility module for safe imports in Python.
"""

__version__ = "0.4.0"

get_version = lambda: __version__

import importlib
from types import ModuleType
from typing import Any, Optional, Protocol, TypeAlias, Union

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

    @property
    def raises(self) -> bool:
        """
        Enable raising exceptions for the current state.
        """
        self._raise_exc


class _Future(Protocol):
    """
    A sentinel class to represent a future value that has not yet been set.
    """

    pass


class NotFound(_Future):
    """
    A sentinel class to represent a value that has not been found in the import context.
    """

    pass


state = _State()


class Import:
    """
    Context manager for scoped safe imports.
    """

    def __init__(self, main: str, fallback: str, raises: bool = True):
        self.main = main
        self.fallback = fallback
        self._old_state = None
        if not raises:
            state.catch()

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


def __getattr__(name: str, state: _State | None = None) -> SafeEntity:
    """
    Dynamic attribute access for the safelib module.

    Args:
        name (str): The name of the attribute to access.

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
                    return importlib.import_module(name)
                return getattr(importlib.import_module(state.main.value), name)
            except (ImportError, AttributeError, ModuleNotFoundError):
                if not state.fallback.empty:
                    if name == state.fallback.value:
                        try:
                            return importlib.import_module(name)
                        except ImportError:
                            if state.raises:
                                raise ImportError(
                                    f"Module '{state.fallback.value}' not found"
                                )
                            else:
                                return NotFound
                    if state.raises:
                        return getattr(
                            importlib.import_module(state.fallback.value), name
                        )
                    else:
                        return getattr(
                            importlib.import_module(state.fallback.value),
                            name,
                            NotFound,
                        )
                if state.raises:
                    raise ImportError(
                        f"Module '{state.main.value}' has no attribute '{name}'"
                    )
                else:
                    return NotFound
        return _Future
