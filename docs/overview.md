# Overview

PyHTSW (formerly PyHTSL) is a Python frontend that emits **htsw** projects. You
write Python; running the script produces an htsw project folder that the HTSW
tooling imports into a Hypixel Housing.

htsw is a text format for Housing entities (functions, events, items, regions,
menus, NPCs) built around two formats: `import.json` and HTSL. PyHTSW generates
both for you — you never edit them by hand.

```python
import pyhtsw
from pyhtsw import create_function, chat


@create_function('Welcome')
def welcome() -> None:
    chat('&aWelcome to my house!')
```

Running this writes a project with a `Welcome` function whose actions live in an
HTSL file. See [Exporting](./exporting.md) for the generated layout.

See also the vendored htsw reference: [HTSW Overview](./htsw/overview.md).
