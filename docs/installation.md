# Installation

PyHTSW requires **Python 3.13+**. Make sure Git is on your PATH, then install:

```sh
pip install "git+https://github.com/69Jesse/PyHTSW.git" --upgrade
```

Then `import pyhtsw` from any script.

## Where output goes

Running a script writes an htsw project folder into your projects folder. By
default this is `.minecraft/htsw/projects` (resolved per-OS). Override it with
`set_projects_folder(path)`. See [Exporting](./exporting.md) for details.
