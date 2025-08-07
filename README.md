##  SafeLib - Import Everything Safe

Safelib is an importer that supports fallback mechanism.

[![PyPI Downloads](https://static.pepy.tech/badge/safelib)](https://pepy.tech/projects/safelib) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/fswair/safelib)

### 0.6.0 Changelog

* Fixed several issues
* Added safelib.valid instead importer.valid
* Added search_builtins feature
* Extended exception handling

## Example Usage

### Using Context Manager (sync/async)
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

### Using Classical Imports

```python
from safelib import _main, typing, _fallback, typing_extensions

from safelib import Protocol, _no_raise

#> Protocol is safelib.NotFound, typing.Protocol or typing_extensions.Protocol

from safelib import _no_raise # catch errors by defaulting missing entities
```

### No-Raise Statement

Import `_no_raise` sentinel to catch exceptions in current state.

```python
from safelib import _main, typing
from safelib import _no_raise, Protocool
# Protocool is safelib.NotFound, otherwise raises exception

import safelib

with safelib.Import(raises=False) as foo:
    # use context manager of Import with raises=False
    # or call safelib.catch() before context manager
    pass
```

### Reset Statement

Import `_reset` sentinel to reset current state of safelib.

```python
from safelib import _main, httpx
# after get method returned, state will be restored to initial state
from safelib import get, _reset 
```

```python
from safelib import Import

async with Import('sqlalchemy', 'peewee') as importer:
    SafeEntity = importer.SafeEntity
    importer.reset_state()
```

For inquiries, feature request and bug reports, please contact me at contact@tomris.dev
