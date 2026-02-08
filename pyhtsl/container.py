import atexit
import os
import sys
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, ClassVar, Protocol, Self

from .config import DISABLE_GLOBAL_EXPORT, DISPLAY_HTSL, get_htsl_import_folder
from .logger import AntiSpamLogger
from .public.function import Function

if TYPE_CHECKING:
    from .expression.expression import Expression


__all__ = (
    'Container',
    'get_current_container',
)


class ContextEntry(Protocol):
    expressions: list['Expression']


class Container:
    name: str

    logger: AntiSpamLogger
    registered_functions: list[Function[Callable[[], None]]]
    expressions: list['Expression']
    contexts: list[ContextEntry]

    exported_names: ClassVar[set[str]] = set()

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name
        self.logger = AntiSpamLogger()
        self.registered_functions = []
        self.expressions = []
        self.contexts = []

    @property
    def is_global(self) -> bool:
        return self is CONTAINERS[0]

    def add_context(self, context: ContextEntry) -> None:
        self.contexts.append(context)

    def remove_context(self, context: ContextEntry) -> None:
        assert self.contexts[-1] is context, 'Context stack is corrupted'
        self.contexts.pop()

    def __enter__(self) -> Self:
        CONTAINERS.append(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        assert CONTAINERS[-1] is self, 'Container stack is corrupted'
        CONTAINERS.pop()

    def into_htsl(self) -> str:
        return '\n'.join(expr.into_htsl() for expr in self.expressions)

    def htsl_path(self) -> Path:
        return get_htsl_import_folder() / f'{self.name}.htsl'

    def export(self) -> None:
        if not self.expressions:
            print(
                'Nothing found to write to your .htsl file. \x1b[38;2;255;0;0mPyHTSL will not do anything.\x1b[0m'
            )
            return

        if self.name in self.exported_names:
            raise RuntimeError(
                f'Container with name "{self.name}" has already been exported.'
                + (
                    ' This is the global export, it is possible to disable the global export with "pyhtsl.disable_global_export()".'
                    if self.is_global
                    else ''
                )
            )
        self.exported_names.add(self.name)

        if self.is_global:
            print(
                f'\n\x1b[38;2;0;255;0mExporting global container named \x1b[38;2;255;0;0m{self.name}\x1b[0m'
            )
        else:
            print(
                f'\n\x1b[38;2;0;255;0mExporting container named \x1b[38;2;255;0;0m{self.name}\x1b[0m'
            )

        args: list[str] = sys.argv[1:]
        content = self.into_htsl()

        path = self.htsl_path()
        path.write_text(
            f'// Generated with PyHTSL https://github.com/69Jesse/PyHTSL\n{content}',
            encoding='utf-8',
        )

        if 'code' in args:
            os.system(f'code "{path.absolute()}"')

        if DISPLAY_HTSL:
            print(content)

        self.logger.publish()

        print(

                '\n\x1b[38;2;0;255;0mAll done! Your .htsl file is written to the following location:\x1b[0m'
                f'\n{path.absolute()}'
                f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{self.name}\x1b[0m'
                '\n'

        )


global_name = os.path.basename(sys.argv[0]).rsplit('.', 1)[0]
CONTAINERS: list[Container] = [Container(name=global_name)]


def get_current_container() -> Container:
    return CONTAINERS[-1]


EXCEPTION_OCCURRED = False


def exception_hook(
    exc_type: type[BaseException],
    exc_value: BaseException,
    traceback: TracebackType | None,
) -> None:
    global EXCEPTION_OCCURRED
    EXCEPTION_OCCURRED = True
    sys.__excepthook__(exc_type, exc_value, traceback)


def on_program_exit() -> None:
    if EXCEPTION_OCCURRED:
        return
    container = get_current_container()
    if not container.is_global:
        raise RuntimeError(
            'Program exited without exporting a non-global container. This should never happen.'
        )

    if DISABLE_GLOBAL_EXPORT:
        print(
            '\x1b[38;2;255;0;0mGlobal export is disabled. No .htsl file will be written.\x1b[0m'
        )
        return

    container.export()


sys.excepthook = exception_hook
atexit.register(on_program_exit)
