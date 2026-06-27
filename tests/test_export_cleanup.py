"""Re-exporting a project removes the files pyhtsw generated on a previous run
that are no longer produced (so HTSW never imports stale `.htsl`/`.snbt`/
`import.json`), while leaving hand-placed files (e.g. `.txt`) untouched."""

import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    chat,
    create_function,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)

root = tmp / 'cleanup-test'

# Simulate a previous export plus user-placed files.
(root / 'functions').mkdir(parents=True)
(root / 'functions' / 'stale.htsl').write_text('// a function that no longer exists')
(root / 'old-item.snbt').write_text('{}')
(root / 'gone').mkdir()
(root / 'gone' / 'dead.htsl').write_text('// whole folder is now stale')
(root / 'notes.txt').write_text('keep me')
(root / 'data').mkdir()
(root / 'data' / 'config.txt').write_text('keep me too')


with Container() as container:

    @create_function('Foo')
    def foo() -> None:
        chat('hi')


container.export('Cleanup Test')

# Current generated files are present.
assert (root / 'functions' / 'foo.htsl').exists()
assert (root / 'import.json').exists()

# Stale generated files (owned types not written this run) are gone.
assert not (root / 'functions' / 'stale.htsl').exists()
assert not (root / 'old-item.snbt').exists()
assert not (root / 'gone' / 'dead.htsl').exists()
# The directory left empty by stale removal is pruned.
assert not (root / 'gone').exists()

# Hand-placed files (and the folders holding them) survive untouched.
assert (root / 'notes.txt').read_text() == 'keep me'
assert (root / 'data' / 'config.txt').read_text() == 'keep me too'
assert (root / 'data').is_dir()

# The only generated (owned) files left on disk are the ones this run produced.
remaining_owned = {
    p.relative_to(root).as_posix()
    for p in root.rglob('*')
    if p.is_file() and (p.suffix in {'.htsl', '.snbt'} or p.name == 'import.json')
}
assert remaining_owned == {'import.json', 'functions/foo.htsl'}, remaining_owned
