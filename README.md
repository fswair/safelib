##  SafeLib - Import Everything Safe

Safelib is an importer that supports fallback mechanism.

## Example Usage

### Using Context Manager (sync/async)
```python
import safelib
from safelib import Import

with Import('typing', 'typing_extensions', raises=False) as importer:
    # use traditional import
    from safelib import Protocol
    
    # use importer to access the final
    final = importer.final

    if not importer.valid(final):
        raise ImportError('Can not import final.')

    # use get_entity function to import override
    override = importer.get_entity('override')
```

### Using Classical Imports

```python
from safelib import _main, typing, _fallback, typing_extensions

from safelib import Protocol

# typing.Protocol or typing_extensions.Protocol
print(Protocol)
```

### Reset State

Import `_reset` sentinel to reset current state of safelib.

```python
from safelib import _main, httpx
# after get method returned, state will be restored to initial state
from safelib import get, _reset 
```

```python
from safelib import Import

async with Import('typing', 'my_types', search_builtins=True) as importer:
    SafeEntity = importer.SafeEntity
    importer.reset_state()
```

For inquiries, feature request and bug reports, please contact me at contact@tomris.dev
