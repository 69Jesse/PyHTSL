# Structuring a project

A one-off script is fine for a small house. Once a project grows past a single
file, give it a real structure so it stays maintainable. The convention below is
what the example projects use.

## A uv project, flat modules

Make each project its own [uv](https://docs.astral.sh/uv/) project with a
`pyproject.toml`, and keep the modules *flat* — the project root is the working
directory, so absolute imports like `from core.constants import X` and
`from features.shop import ...` resolve when you run from the root. Group related
modules into subpackages; do not wrap everything in a `src/` package.

```
my-house/
  main.py                 # names the export and imports every feature
  pyproject.toml
  core/                   # shared stats, constants, helpers
    __init__.py
    constants.py
  features/               # one concern per module (or per subpackage)
    __init__.py
    shop.py
    combat/
      __init__.py
      ...
  items/                  # item/menu definitions
  assets/                 # data files (.nbs, .snbt, .json)
  tools/                  # scripts that do NOT emit htsw (scrapers, generators)
  tests/                  # standalone checks (see the Simulator page)
```

Split large files by concern rather than letting one module grow unbounded.
Put auxiliary tooling that does not contribute to the export (scrapers, schematic
generators, scratch scripts) under `tools/` so the build surface stays clean.

## pyproject.toml

```toml
[project]
name = "my-house"
requires-python = ">=3.13"
dependencies = ["pyhtsw"]

[tool.uv]
package = false           # this is an app, not an importable library

# Only when depending on a local pyhtsw checkout instead of the published package:
[tool.uv.sources]
pyhtsw = { path = "../path/to/PyHTSW", editable = true }

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG001", "COM812"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "single"

[tool.pyright]
# Flat-module layout: the project root is on sys.path at runtime.
extraPaths = ["."]
```

`extraPaths = ["."]` lets the type checker resolve the flat absolute imports
(they resolve at runtime because the root is the working directory).

## main.py wires everything together

Importables register themselves **at import time**. So `main.py` must import every
feature module — anything not imported simply will not appear in the export. The
robust pattern is to have each subpackage's `__init__.py` import its submodules,
then have `main.py` import the subpackages:

```python
import pyhtsw

from core import constants  # noqa: F401
from features import shop, combat  # noqa: F401
from items import menus  # noqa: F401

pyhtsw.set_project_name('my house')
```

`set_project_name(...)` names the global export (otherwise it is named after the
script file). See [Exporting](./exporting.md).

## Cross-module references

`@create_function` / `@create_event` bodies run **lazily at export**, not when the
module is imported. So a function in one module can reference a function defined
in another regardless of import order. If two feature modules genuinely import
each other, put the sibling import at the *bottom* of the module (after the
definitions) to break the cycle — by export time everything is defined.

## Loading data files

Resolve asset paths relative to the *module file*, never the current directory —
the build must work no matter where it is run from:

```python
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / 'assets'
rooms = (DATA_DIR / 'rooms.json').read_text(encoding='utf-8')
```
