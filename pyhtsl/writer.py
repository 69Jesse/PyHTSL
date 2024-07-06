import os
from pathlib import Path
import atexit
import sys
from .line_type import LineType
from .fixer import Fixer

from types import TracebackType
from typing import Optional, Callable


__all__ = (
    'HERE',
    'HTSL_IMPORTS_FOLDER',
    'WRITER',
)


HERE: Path = Path(__file__).parent

if os.name == 'nt':
    DOT_MINECRAFT: Path = Path(os.getenv('APPDATA')) / '.minecraft'  # type: ignore
elif os.name == 'posix':
    DOT_MINECRAFT: Path = Path.home() / 'Library' / 'Application Support' / 'minecraft'
else:
    raise OSError('Unsupported operating system')
if not DOT_MINECRAFT.exists():
    raise FileNotFoundError('Could not find your minecraft folder')

HTSL_IMPORTS_FOLDER: Path = DOT_MINECRAFT / 'config' / 'ChatTriggers' / 'modules' / 'HTSL' / 'imports'
if not HTSL_IMPORTS_FOLDER.exists():
    raise FileNotFoundError('Could not find your HTSL imports folder')

PYHTSL_FOLDER: Path = HTSL_IMPORTS_FOLDER / 'pyhtsl'
if not PYHTSL_FOLDER.exists():
    PYHTSL_FOLDER.mkdir()


class Writer:
    lines: list[tuple[str, LineType]] = []
    exception_raised: bool = False
    registered_functions: list[Callable[[], None]] = []
    in_front_index: int = 0
    file_name: str
    htsl_file: Path
    python_save_file: Path
    def write(
        self,
        line: str,
        line_type: LineType,
        *,
        append_to_previous_line: bool = False,
        add_to_front: bool = False,
    ) -> None:
        if append_to_previous_line:
            assert not add_to_front
            self.lines[-1] = (self.lines[-1][0] + ' ' + line, line_type)
        else:
            if add_to_front:
                self.lines.insert(self.in_front_index, (line, line_type))
                self.in_front_index += 1
            else:
                self.lines.append((line, line_type))

    def write_to_files(self) -> bool:
        if not self.lines:
            print('Nothing found to write to your .htsl file. \x1b[38;2;255;0;0mPyHTSL will not do anything.\x1b[0m')
            return False

        self.file_name = os.path.basename(sys.argv[0]).rsplit('.', 1)[0]

        args: list[str] = sys.argv[1:]
        if 'lines' in args and self.lines:
            max_line_length: int = max(len(line) for line, _ in self.lines)
            content = '\n'.join(
                f'{line.ljust(max_line_length)}  // {line_type}'
                for line, line_type in self.lines
            )
        else:
            content = '\n'.join((line for line, _ in self.lines))

        encoding: str = 'utf-8'
        self.htsl_file = HTSL_IMPORTS_FOLDER / f'{self.file_name}.htsl'
        self.htsl_file.write_text(
            f'// Generated with PyHTSL https://github.com/69Jesse/PyHTSL\n{content}',
            encoding=encoding,
        )
        if 'code' in args:
            os.system(f'code "{self.htsl_file.absolute()}"')

        self.python_save_file = PYHTSL_FOLDER / f'{self.file_name}.py'
        index: int = 1
        while self.python_save_file.exists():
            index += 1
            self.python_save_file = PYHTSL_FOLDER / f'{self.file_name}_{index}.py'
        self.python_save_file.write_text(Path(sys.argv[0]).read_text(encoding=encoding), encoding=encoding)

        return True

    def exception_hook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: Optional[TracebackType],
    ) -> None:
        self.exception_raised = True
        sys.__excepthook__(exc_type, exc_value, traceback)

    def on_program_exit(self) -> None:
        if self.exception_raised:
            return
        for func in self.registered_functions:
            func()

        fixer = Fixer(self.lines)
        self.lines = fixer.fix()

        if not self.write_to_files():
            return
        print((
            '\n\x1b[38;2;0;255;0mAll done! Your .htsl file is written to the following location:\x1b[0m'
            f'\n{self.htsl_file.absolute()}'
            f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{self.file_name}\x1b[0m'
            '\n'
        ))


WRITER = Writer()
sys.excepthook = WRITER.exception_hook
atexit.register(WRITER.on_program_exit)
