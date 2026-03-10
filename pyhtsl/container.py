import atexit
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, ClassVar, NamedTuple, Self

from .actions.function import Function
from .config import (
    get_htsl_import_folder,
    should_disable_global_export,
    should_display_htsl,
)
from .logger import AntiSpamLogger

if TYPE_CHECKING:
    from .expression.expression import Expression


__all__ = (
    'Container',
    'get_current_container',
)


class ExpressionContext(NamedTuple):
    parent_expression: 'Expression'
    expressions_ref: list['Expression']
    add_expression_to_container: bool = True


class Container:
    name: str

    logger: AntiSpamLogger
    registered_functions: list[Function[Callable[[], None]]]
    expressions: list['Expression']
    contexts: list[ExpressionContext]

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

    def get_expressions_ref_in_context(self, *, go_back: int = 0) -> list['Expression']:
        if go_back >= len(self.contexts):
            return self.expressions
        return self.contexts[-1 - go_back].expressions_ref

    def write_expression(self, expression: 'Expression') -> None:
        self.get_expressions_ref_in_context().append(expression)

    def add_context(self, context: ExpressionContext) -> None:
        self.contexts.append(context)

    def pop_context(self) -> ExpressionContext:
        assert len(self.contexts) > 0, 'Context stack is empty'
        return self.contexts.pop()

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
        lines = ('\n'.join(expr.into_htsl() for expr in self.expressions)).split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].lstrip().startswith('// @ignore'):
                lines.pop(i)
        return '\n'.join(lines)

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

        if should_display_htsl():
            print(content)

        self.logger.publish()

        print(
            '\n\x1b[38;2;0;255;0mAll done! Your .htsl file is written to the following location:\x1b[0m'
            f'\n{path.absolute()}'
            f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{self.name}\x1b[0m'
            '\n'
        )


class ContainerContextManager(ABC):
    @abstractmethod
    def create_context(self) -> ExpressionContext:
        raise NotImplementedError()

    def __enter__(self) -> None:
        context = self.create_context()
        container = get_current_container()
        if context.add_expression_to_container:
            container.write_expression(context.parent_expression)
        container.add_context(context)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        container = get_current_container()
        container.pop_context()


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

    if should_disable_global_export():
        print(
            '\x1b[38;2;255;0;0mGlobal export is disabled. No .htsl file will be written.\x1b[0m'
        )
        return

    container.export()


sys.excepthook = exception_hook
atexit.register(on_program_exit)
