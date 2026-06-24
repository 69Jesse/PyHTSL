# Installation

PyHTSW requires **Python 3.13+**. Make sure Git is on your PATH, then install:

```sh
pip install "git+https://github.com/69Jesse/PyHTSW.git" --upgrade
```

Then `import pyhtsw` from any script.

For anything beyond a one-off script, set the project up as a uv project — see
[Structuring a project](./project-structure.md).

> **Editable installs:** if you install pyhtsw editable (`pip install -e` or a uv
> path source) and a run produces stale output after you change code, you are
> likely importing a cached `.pyc`. Run with `python -B`, or reinstall, to be
> sure you are testing the current source.

## Where output goes

Running a script writes an htsw project folder into your projects folder. By
default this is `.minecraft/htsw/projects` (resolved per-OS). Override it with
`set_projects_folder(path)`. See [Exporting](./exporting.md) for details.
