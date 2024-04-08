import os
from pathlib import Path
import atexit
import sys


__all__ = (
    'write',
)


DOT_MINECRAFT: Path = Path(os.getenv('APPDATA')) / '.minecraft'  # type: ignore
if not DOT_MINECRAFT.exists():
    raise FileNotFoundError('Could not find your .minecraft folder')
HTSL_IMPORTS_FOLDER: Path = DOT_MINECRAFT / 'config' / 'ChatTriggers' / 'modules' / 'HTSL' / 'imports'
if not HTSL_IMPORTS_FOLDER.exists():
    raise FileNotFoundError('Could not find your HTSL imports folder')
PYHTSL_FOLDER: Path = HTSL_IMPORTS_FOLDER / 'pyhtsl'
if not PYHTSL_FOLDER.exists():
    PYHTSL_FOLDER.mkdir()
FILE_NAME: str = os.path.basename(sys.argv[0]).rsplit('.', 1)[0]

HTSL_FILE: Path = HTSL_IMPORTS_FOLDER / f'{FILE_NAME}.htsl'
HTSL_FILE.write_text('// Generated with PyHTSL https://github.com/69Jesse/PyHTSL')

PYTHON_SAVE_FILE: Path = PYHTSL_FOLDER / f'{FILE_NAME}.py'
index: int = 1
while PYTHON_SAVE_FILE.exists():
    index += 1
    PYTHON_SAVE_FILE = PYHTSL_FOLDER / f'{FILE_NAME}_{index}.py'
del index
PYTHON_SAVE_FILE.write_text(Path(sys.argv[0]).read_text())


def write(
    line: str,
    *,
    append_to_previous_line: bool = False,
) -> None:
    with open(HTSL_FILE, 'a') as file:
        if append_to_previous_line:
            file.write(' ' + line)
        else:
            file.write('\n' + line)


@atexit.register
def on_exit() -> None:
    print((
        '\nAll done! Your HTSL file is written to the following location:'
        f'\n{HTSL_FILE.absolute()}'
        f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{FILE_NAME}\x1b[0m'
    ))
