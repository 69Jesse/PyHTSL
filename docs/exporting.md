# Exporting

## The project model

Running a PyHTSW script builds a **project** and, on program exit, writes it as a
folder into your projects folder. HTSW imports that folder.

- Default projects folder: `.minecraft/htsw/projects` (resolved per-OS).
- Override it:

```python
from pyhtsw import set_projects_folder

set_projects_folder('/path/to/.minecraft/htsw/projects')
```

The chosen folder is cached so you only set it once.

The project name is derived from your script filename, or set it explicitly with
`set_project_name('my house')` (call it once, e.g. in `main.py`). The folder is
written to `<projects-folder>/<kebab-name>/`.

## Generated folder layout

```
<project>/
  import.json
  functions/<name>.htsl
  events/<name>.htsl
  items/<name>.snbt
  regions/<name>/enter.htsl
  regions/<name>/exit.htsl
  menus/<name>/slot-<row>-<col>.htsl
  npcs/<name>/left.htsl
  npcs/<name>/right.htsl
```

- `import.json` ties everything together; each importable points at its action
  files.
- Names are kebab-cased for file paths.
- Action bodies are `.htsl` files; item definitions are `.snbt` files.
- Empty action blocks are omitted.

See the [HTSW Importables reference](./htsw/importables.md) for the import.json
schema.

## Top-level actions

Actions written outside any importable (not inside a `@create_function`,
`@create_event`, item handler, etc.) get wrapped into a single function named
after the project, and PyHTSW logs a warning. Put them inside an importable to
silence it:

```python
from pyhtsw import create_function, chat


@create_function('Setup')
def setup() -> None:
    chat('hello')  # belongs to the Setup function, no warning
```

## Building and validating

Run the script to build:

```sh
uv run python main.py     # or: python main.py
```

The run prints, near the end, the absolute path it wrote the project to. Validate
that output with the htsw CLI before importing it in-game (see the
[HTSW tooling reference](./htsw/tooling.md)):

```sh
htsw check <printed-path>/import.json
```

A clean project reports `OK`. Note:

- Functions that exceed the per-block action limit are **split automatically**
  into `Foo`, `Foo 2`, `Foo 3`, … — this is expected, not an error.
- Large projects can take a while to build; the optimizer does most of the work.

## Refactoring safely

When reorganising a project, the goal is byte-equivalent output. Confirm it by
diffing a build against a baseline taken *before* the change:

- The set of importable names in `import.json` (functions, events, items, menus,
  …) must be **identical** — a missing name means a module is no longer imported
  by `main.py`.
- The `htsw check` result must not gain any new errors.

## Disabling export

To build a project without writing anything (e.g. in tests), call
`disable_global_export()` before exit.
