import os
from pathlib import Path
import atexit
import sys
from .line_type import LineType
from .fixer import Fixer
from .logger import AntiSpamLogger
from .public.display_htsl import should_display_htsl

from types import TracebackType
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from .public.function import Function


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


class ExportContainer:
    name: str
    is_global: bool
    lines: list[tuple[str, LineType]]
    registered_functions: list['Function']
    in_front_index: int
    indent: int
    logger: AntiSpamLogger
    def __init__(
        self,
        name: str,
        *,
        is_global: bool = False,
    ) -> None:
        self.name = name
        self.is_global = is_global
        self.lines = []
        self.registered_functions = []
        self.in_front_index = 0
        self.indent = 0
        self.logger = AntiSpamLogger()

    def htsl_path(self) -> Path:
        return HTSL_IMPORTS_FOLDER / f'{self.name}.htsl'


class TemporaryContainerContextManager:
    writer: 'Writer'
    name: str
    def __init__(
        self,
        writer: 'Writer',
        name: str,
    ) -> None:
        self.writer = writer
        self.name = name

    def __enter__(self) -> ExportContainer:
        container = ExportContainer(self.name)
        self.writer.containers.append(container)
        return container

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        container = self.writer.get_container()
        if container.name != self.name:
            raise RuntimeError(f'Container "{self.name}" was not the last one created. This should never happen.')
        self.writer.containers.pop()


class Writer:
    containers: list[ExportContainer]
    exception_raised: bool
    export_globally: bool
    exported_names: set[str]

    def __init__(self) -> None:
        global_name = os.path.basename(sys.argv[0]).rsplit('.', 1)[0]
        self.containers = [ExportContainer(global_name, is_global=True)]
        self.exception_raised = False
        self.export_globally = True
        self.exported_names = set()

    def get_container(self) -> ExportContainer:
        if not self.containers:
            raise RuntimeError('No containers available. This should never happen.')
        return self.containers[-1]

    def temporary_container_context(
        self,
        name: str,
    ) -> TemporaryContainerContextManager:
        return TemporaryContainerContextManager(self, name)

    def write(
        self,
        line: str,
        line_type: LineType,
        *,
        append_to_previous_line: bool = False,
        add_to_front: bool = False,
    ) -> None:
        container = self.get_container()

        line = ('    ' * container.indent) + line

        if append_to_previous_line:
            assert not add_to_front
            container.lines[-1] = (container.lines[-1][0] + ' ' + line, line_type)
        else:
            if add_to_front:
                container.lines.insert(container.in_front_index, (line, line_type))
                container.in_front_index += 1
            else:
                container.lines.append((line, line_type))

    def get_content(self, container: ExportContainer) -> str:
        return '\n'.join((line for line, _ in container.lines))

    def write_htsl(self, container: ExportContainer) -> bool:
        if not container.lines:
            print('Nothing found to write to your .htsl file. \x1b[38;2;255;0;0mPyHTSL will not do anything.\x1b[0m')
            return False

        args: list[str] = sys.argv[1:]
        content = self.get_content(container)

        path = container.htsl_path()
        path.write_text(f'// Generated with PyHTSL https://github.com/69Jesse/PyHTSL\n{content}', encoding='utf-8')

        if 'code' in args:
            os.system(f'code "{path.absolute()}"')

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
        container = self.get_container()
        if not container.is_global:
            raise RuntimeError('Program exited without exporting a non-global container. This should never happen.')
        if not self.export_globally:
            print('\x1b[38;2;255;0;0mGlobal export is disabled. No .htsl file will be written.\x1b[0m')
            return
        self.run_export(container)

    def run_export(self, container: ExportContainer) -> None:
        if container.name in self.exported_names:
            raise RuntimeError(
                f'Container with name "{container.name}" has already been exported.'
                + (' This is the global export, it is possible to disable the global export with "pyhtsl.disable_global_export()".' if container.is_global else '')
            )

        if not container.is_global:
            print(f'\n\x1b[38;2;0;255;0mExporting container named \x1b[38;2;255;0;0m{container.name}\x1b[0m')
        else:
            print(f'\n\x1b[38;2;0;255;0mExporting global container named \x1b[38;2;255;0;0m{container.name}\x1b[0m')

        for function in container.registered_functions:
            if function.callback is None:
                raise RuntimeError(f'Function "{function.name}" has no callback. Unable to export.')
            function.callback()

        fixer = Fixer(container)
        container.lines = fixer.fix()

        if not self.write_htsl(container):
            return

        if should_display_htsl():
            print(self.get_content(container))
        container.logger.publish()

        path = container.htsl_path()
        print((
            '\x1b[38;2;0;255;0mAll done! Your .htsl file is written to the following location:\x1b[0m'
            f'\n{path.absolute()}'
            f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{container.name}\x1b[0m'
            '\n'
        ))

        self.exported_names.add(container.name)

    def begin_indent(self) -> None:
        self.indent += 1

    def end_indent(self) -> None:
        self.indent -= 1


WRITER = Writer()
sys.excepthook = WRITER.exception_hook
atexit.register(WRITER.on_program_exit)
