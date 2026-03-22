import atexit
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, ClassVar, NamedTuple, Self

from .config import (
    get_htsl_import_folder,
    should_disable_global_export,
    should_display_htsl,
)
from .logger import AntiSpamLogger
from .utils.slug import into_slug

if TYPE_CHECKING:
    from .block import Block
    from .expression.expression import Expression


__all__ = (
    'Container',
    'get_current_container',
)


WRITE_EXPRESSION_OVERRIDE_STACK: list[Callable[['Expression'], None]] = []


@contextmanager
def override_write_expression(
    func: Callable[['Expression'], None],
) -> Generator[None, None, None]:
    WRITE_EXPRESSION_OVERRIDE_STACK.append(func)
    try:
        yield
    finally:
        WRITE_EXPRESSION_OVERRIDE_STACK.pop()


class ExpressionContext(NamedTuple):
    parent_expression: 'Expression | None'
    expressions_ref: list['Expression']
    add_expression_to_container: bool = True


class Container:
    exported_names: ClassVar[set[str]] = set()

    logger: AntiSpamLogger
    blocks: list['Block']
    contexts: list[ExpressionContext]

    is_finalized: bool

    def __init__(self) -> None:
        from .block import GlobalBlock

        self.logger = AntiSpamLogger()
        self.blocks = [GlobalBlock()]
        self.contexts = []
        self.is_finalized = False

    @property
    def is_global(self) -> bool:
        return self is CONTAINERS[0]

    def get_expressions_ref_in_context(self, *, go_back: int = 0) -> list['Expression']:
        if go_back >= len(self.contexts):
            return self.blocks[0].expressions
        return self.contexts[-1 - go_back].expressions_ref

    def write_expression(self, expression: 'Expression') -> None:
        if WRITE_EXPRESSION_OVERRIDE_STACK:
            WRITE_EXPRESSION_OVERRIDE_STACK[-1](expression)
            return

        if self.is_finalized:
            raise RuntimeError(
                'Container is already finalized, cannot write new expressions'
            )

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
        self.finalize()
        CONTAINERS.pop()

    def finalize_expressions(self, expressions: list['Expression']) -> None:
        def on_new_expression(expression: 'Expression') -> None:
            nonlocal index
            expressions.insert(index, expression)
            index += 1

        index = len(expressions) - 1
        with override_write_expression(on_new_expression):
            while index >= 0:
                expression = expressions[index]
                expression.finalize(self)
                index -= 1

    def finalize(self) -> None:
        if self.is_finalized:
            raise RuntimeError('Container is already finalized')
        for block in self.blocks:
            block.finalize(self)
        self.is_finalized = True

    @staticmethod
    def prettify_htsl_lines(lines: list[str]) -> None:
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].lstrip().startswith('// @ignore'):
                lines.pop(i)

    def into_htsl(self) -> str:
        if not self.is_finalized:
            raise RuntimeError(
                'Unable to transform Container into htsl: Container is not finalized. Either exit the container context or call "finalize()" manually'
            )

        for block in self.blocks:
            block.fix_action_limits()

        with override_write_expression(lambda _: None):
            lines = ('\n\n\n'.join(block.into_htsl() for block in self.blocks)).split(
                '\n'
            )

        self.prettify_htsl_lines(lines)
        return '\n'.join(lines)

    def htsl_path(self, name: str) -> Path:
        return get_htsl_import_folder() / f'{name}.htsl'

    def export(self, name: str) -> None:
        if not self.blocks:
            print(
                'Nothing found to write to your .htsl file. \x1b[38;2;255;0;0mPyHTSL will not do anything.\x1b[0m'
            )
            return

        if name in self.exported_names:
            raise RuntimeError(
                f'Container with name "{name}" has already been exported.'
                + (
                    ' This is the global export, it is possible to disable the global export with "pyhtsl.disable_global_export()".'
                    if self.is_global
                    else ''
                )
            )
        self.exported_names.add(name)

        if self.is_global:
            print(
                f'\n\x1b[38;2;0;255;0mExporting global container named \x1b[38;2;255;0;0m{name}\x1b[0m'
            )
        else:
            print(
                f'\n\x1b[38;2;0;255;0mExporting container named \x1b[38;2;255;0;0m{name}\x1b[0m'
            )

        args: list[str] = sys.argv[1:]
        content = self.into_htsl()

        path = self.htsl_path(name)
        path.write_text(
            f'// Generated with PyHTSL https://github.com/69Jesse/PyHTSL\n{content}\n',
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
            f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{name}\x1b[0m'
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
            assert context.parent_expression is not None
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


GLOBAL_NAME = into_slug(os.path.basename(sys.argv[0]).rsplit('.', 1)[0])
CONTAINERS: list[Container] = [Container()]


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

    container.finalize()
    container.export(GLOBAL_NAME)


sys.excepthook = exception_hook
atexit.register(on_program_exit)
