import os
from pathlib import Path
import atexit
import sys
import re
from .line_type import LineType
from .fixer import Fixer, LOGGER
from .public.display_htsl import should_display_htsl

from types import TracebackType
from typing import Optional, Callable


__all__ = (
    'set_htsl_imports_folder',
    'LineType',
    'WRITER',
)


HERE: Path = Path(__file__).parent
CACHED_HTSL_IMPORTS_FOLDER_PATH: Path = HERE / 'cached_htsl_imports_folder.txt'


def set_htsl_imports_folder(htsl_folder: Path | str) -> None:
    if isinstance(htsl_folder, str):
        htsl_folder = Path(htsl_folder)
    if not htsl_folder.is_dir():
        raise NotADirectoryError('The provided HTSL imports folder is not a directory.')
    if not htsl_folder.exists():
        raise FileNotFoundError('The provided HTSL imports folder does not exist.')
    content = CACHED_HTSL_IMPORTS_FOLDER_PATH.read_text() if CACHED_HTSL_IMPORTS_FOLDER_PATH.exists() else None
    new_content = htsl_folder.resolve().as_posix()
    if content is not None and content == new_content:
        return
    CACHED_HTSL_IMPORTS_FOLDER_PATH.write_text(new_content)
    print(f'Saved your HTSL imports folder \x1b[38;2;0;255;0m{htsl_folder.as_posix()}\x1b[0m for future use at\n\x1b[38;2;0;255;0m{CACHED_HTSL_IMPORTS_FOLDER_PATH}\x1b[0m')


def get_htsl_import_folder() -> Path:
    maybe_path: Path | None = None
    if CACHED_HTSL_IMPORTS_FOLDER_PATH.exists():
        raw_path = CACHED_HTSL_IMPORTS_FOLDER_PATH.read_text().strip()
        if raw_path:
            maybe_path = Path(raw_path)
    elif os.name == 'nt':
        maybe_path = Path(os.getenv('APPDATA')) / '.minecraft' / 'config' / 'ChatTriggers' / 'modules' / 'HTSL' / 'imports'  # type: ignore
    elif os.name == 'posix':
        maybe_path = Path.home() / 'Library' / 'Application Support' / 'minecraft' / 'config' / 'ChatTriggers' / 'modules' / 'HTSL' / 'imports'

    if maybe_path is not None:
        maybe_path = maybe_path.resolve()
        if maybe_path.exists():
            set_htsl_imports_folder(maybe_path)
            return maybe_path

    print('\x1b[38;2;255;0;0mCould not find your HTSL imports folder.\x1b[0m')
    while True:
        raw_path = input('Please enter the path to your \x1b[38;2;0;255;0mHTSL imports folder\x1b[0m (relative or absolute): ').strip()
        if not raw_path:
            print('\x1b[38;2;255;0;0mPlease provide a valid path.\x1b[0m')
            continue
        maybe_path = Path(raw_path).resolve()
        try:
            set_htsl_imports_folder(maybe_path)
            return maybe_path
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f'\x1b[38;2;255;0;0m{e.__class__.__name__}: {e}\x1b[0m')
            continue


HTSL_IMPORTS_FOLDER: Path = get_htsl_import_folder()
if not HTSL_IMPORTS_FOLDER.exists():
    raise FileNotFoundError(f'Could not find your HTSL imports folder at\n{HTSL_IMPORTS_FOLDER}')


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

    def get_content(self) -> str:
        return '\n'.join((line for line, _ in self.lines))

    def write_to_files(self) -> bool:
        if not self.lines:
            print('Nothing found to write to your .htsl file. \x1b[38;2;255;0;0mPyHTSL will not do anything.\x1b[0m')
            return False

        self.file_name = os.path.basename(sys.argv[0]).rsplit('.', 1)[0]

        args: list[str] = sys.argv[1:]
        content = self.get_content()

        if 'functions' in args:
            lines = content.split('\n')
            names_seen: set[str] = set()
            regex = re.compile(r'goto function "(.+)"')
            new_lines: list[str] = []
            for line in lines:
                match = regex.match(line)
                if not match:
                    continue
                name = match.group(1)
                if name in names_seen:
                    continue
                names_seen.add(name)
                new_lines.append(line)
            content = '\n'.join(new_lines)

        encoding: str = 'utf-8'
        self.htsl_file = HTSL_IMPORTS_FOLDER / f'{self.file_name}.htsl'
        self.htsl_file.write_text(
            f'// Generated with PyHTSL https://github.com/69Jesse/PyHTSL\n{content}',
            encoding=encoding,
        )
        if 'code' in args:
            os.system(f'code "{self.htsl_file.absolute()}"')

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

        if should_display_htsl():
            print(self.get_content())
        LOGGER.publish()

        print((
            '\n\x1b[38;2;0;255;0mAll done! Your .htsl file is written to the following location:\x1b[0m'
            f'\n{self.htsl_file.absolute()}'
            f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{self.file_name}\x1b[0m'
            '\n'
        ))


WRITER = Writer()
sys.excepthook = WRITER.exception_hook
atexit.register(WRITER.on_program_exit)
