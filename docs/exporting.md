# Exporting

## The project model

Running a PyHTSW script builds a **project** and, on program exit, writes it as a
folder into your projects folder. HTSW imports that folder.

- Default projects folder: `.minecraft/htsw/projects` (resolved per-OS).
- Set it once for this machine:

```python
from pyhtsw import set_projects_folder

set_projects_folder('/path/to/.minecraft/htsw/projects', save=True)
```

`save=True` remembers the folder for future runs. Without it the folder applies
to the current run only, so a test or benchmark can point exports somewhere
harmless without disturbing your real projects folder. A single container can
also name its own, which needs no global state at all:

```python
with Container(projects_folder='/tmp/throwaway') as container:
    ...
```

The project name is derived from your script filename, or set it explicitly with
`configure(project_name='my house')`. The folder is written to
`<projects-folder>/<kebab-name>/`.

## Configuration

Everything about *how* a project is exported belongs to the container that is
exported, and is spelled as a plain attribute, a constructor keyword, or a
`configure(...)` call — whichever reads best:

```python
import pyhtsw

pyhtsw.configure(
    project_name='humanity',
    house_uuid='b8e7bfe4-ab9e-4a58-9026-3aba9ab52b65',
    cleanup_stale_files=True,
)

# the same thing, one field at a time
container = pyhtsw.get_global_container()
container.project_name = 'humanity'

# or scoped to one container
with pyhtsw.Container(project_name='side project') as side:
    ...
```

| Setting | Default | What it does |
| --- | --- | --- |
| `project_name` | script filename | Names the export |
| `house_uuid` | `None` | Binds the entry `import.json` to one house |
| `projects_folder` | machine setting | Where this container's project folder is written |
| `cleanup_stale_files` | `False` | Delete generated files a previous export left behind |
| `display_output` | `False` | Print every generated file to the console |
| `auto_export` | `True` | Export on program exit (global container only) |
| `ignore_action_limits` | `False` | Skip the action-limit check |
| `ignore_scope` | `False` | Skip the scope check |
| `allow_nested_expressions` | `False` | Permit nested if/random blocks |

A container that sets nothing of its own reads through to the **global
container**, so one `pyhtsw.configure(...)` at the top of `main.py` still answers
for every sub-export. `project_name` is the exception: it is never inherited, or
two containers would export over one another.

`cleanup_stale_files` and `display_output` can also be passed to a single
`export()` call, which wins over both:

```python
container.export('MyHouse', cleanup_stale_files=True, display_output=True)
```

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

See htsw's `language/src/importjson/schemaSpec.ts` for the import.json
schema.

## Top-level actions

Actions written outside any importable (not inside a `@function`,
`@event`, item handler, etc.) get wrapped into a single function named
after the project (the `project_name` setting, else the script filename), and
PyHTSW raises a `PyHTSWWarning` pointing at the first such line. Put them
inside an importable to silence it:

```python
from pyhtsw import function, chat


@function('Setup')
def setup() -> None:
    chat('hello')  # belongs to the Setup function, no warning
```

## Building and checking

To check the result of your code — i.e. confirm it produces a valid project —
build it, then run the htsw checker on what it built. There is no separate
"check" step in pyhtsw: you always build first, because the checker validates the
generated `import.json`.

1. Build by running the script:

   ```sh
   uv run python main.py     # or: python main.py
   ```

2. The run prints, near the end, the absolute path it wrote the project to. Run
   the htsw checker on that project's `import.json`:

   ```sh
   htsw check <printed-path>/import.json
   ```

A clean project reports `OK`; otherwise the checker lists the problems. Note:

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
`disable_global_export()` before exit — shorthand for setting `auto_export` to
`False` on the global container.
