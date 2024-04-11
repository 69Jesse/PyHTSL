import os
from pathlib import Path
import atexit
import sys

from types import TracebackType
from typing import Optional, Callable


__all__ = (
    'WRITER',
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


class Writer:
    lines: list[str] = []
    exception_raised: bool = False
    registered_functions: list[Callable[[], None]] = []
    in_front_index: int = 0
    file_name: str
    htsl_file: Path
    python_save_file: Path
    def write(
        self,
        line: str,
        *,
        append_to_previous_line: bool = False,
        add_to_front: bool = False,
    ) -> None:
        if append_to_previous_line:
            assert not add_to_front
            self.lines[-1] += ' ' + line
        else:
            if add_to_front:
                self.lines.insert(self.in_front_index, line)
                self.in_front_index += 1
            else:
                self.lines.append(line)

    def write_to_files(self) -> None:
        self.file_name = os.path.basename(sys.argv[0]).rsplit('.', 1)[0]

        self.htsl_file = HTSL_IMPORTS_FOLDER / f'{self.file_name}.htsl'
        self.htsl_file.write_text(
            '// Generated with PyHTSL https://github.com/69Jesse/PyHTSL\n'
            + '\n'.join(self.lines)
        )

        self.python_save_file = PYHTSL_FOLDER / f'{self.file_name}.py'
        index: int = 1
        while self.python_save_file.exists():
            index += 1
            self.python_save_file = PYHTSL_FOLDER / f'{self.file_name}_{index}.py'
        self.python_save_file.write_text(Path(sys.argv[0]).read_text())

    def exception_hook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: Optional[TracebackType],
    ) -> None:
        self.exception_raised = True
        sys.__excepthook__(exc_type, exc_value, traceback)

    def on_exit(self) -> None:
        if self.exception_raised:
            return
        for func in self.registered_functions:
            func()
        self.write_to_files()
        print((
            '\nAll done! Your .htsl file is written to the following location:'
            f'\n{self.htsl_file.absolute()}'
            f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{self.file_name}\x1b[0m'
            '\n'
        ))


WRITER = Writer()
sys.excepthook = WRITER.exception_hook
atexit.register(WRITER.on_exit)
