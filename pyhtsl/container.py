import atexit
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, ClassVar, NamedTuple, NoReturn, Self

from .config import (
    get_htsl_import_folder,
    should_disable_global_export,
    should_display_htsl,
)
from .logger import AntiSpamLogger
from .utils.log import log
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
    ignore_action_limits: bool
    allow_nested_expressions: bool

    def __init__(
        self,
        *,
        ignore_action_limits: bool = False,
        allow_nested_expressions: bool = False,
    ) -> None:
        from .block import GlobalBlock

        self.logger = AntiSpamLogger()
        self.blocks = []
        self.add_block(GlobalBlock())
        self.contexts = []

        self.is_finalized = False
        self.allow_nested_expressions = allow_nested_expressions
        self.ignore_action_limits = ignore_action_limits

    def expressions(self) -> list['Expression']:
        def throw() -> NoReturn:
            raise RuntimeError(
                'Shortcut "Container.expressions" should only be used when there is exactly one non-empty block in the container'
                ', since it would be ambiguous otherwise. Use "Container.blocks" to access the blocks directly and get their expressions.'
            )

        found_block: Block | None = None
        expressions: list[Expression] = []
        for block in self.blocks:
            if block.is_empty():
                continue
            if block._overflow_root_ref is not None:
                if found_block is None or block._overflow_root_ref is not found_block:
                    throw()
                expressions.extend(block.expressions)
                continue
            if found_block is not None:
                throw()
            found_block = block
            expressions.extend(block.expressions)

        if found_block is None:
            throw()

        return expressions

    def expression_counts(
        self,
        *,
        nested: bool = False,
    ) -> dict[type['Expression'], int]:
        counts: dict[type[Expression], int] = {}
        for block in self.blocks:
            for cls, count in block.expression_counts(nested=nested).items():
                counts[cls] = counts.get(cls, 0) + count
        return counts

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
            return

        self.get_expressions_ref_in_context().append(expression)

    def add_block(self, block: 'Block', *, index: int | None = None) -> None:
        block.container = self
        if index is None:
            self.blocks.append(block)
        else:
            self.blocks.insert(index, block)

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
        from .actions.no_optimization import no_optimization
        from .expression.binary_expression import BinaryExpression

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

        if not no_optimization():
            BinaryExpression.optimize_binary_expressions(expressions)

    def finalize(self) -> None:
        if self.is_finalized:
            raise RuntimeError('Container is already finalized')
        for index, block in enumerate(self.blocks):
            block.finalize(self, index)
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

        with override_write_expression(lambda _: None):
            lines = (
                '\n\n\n'.join(
                    block.into_htsl() for block in self.blocks if not block.is_empty()
                )
            ).split('\n')

        self.prettify_htsl_lines(lines)
        return '\n'.join(lines)

    def htsl_path(self, name: str) -> Path:
        return get_htsl_import_folder() / f'{name}.htsl'

    def is_empty(self) -> bool:
        return all(block.is_empty() for block in self.blocks)

    def export(self, name: str) -> None:
        if self.is_empty():
            log(
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

        log(
            f'\n\x1b[38;2;0;255;0mExporting {"global " * (self.is_global)}container named \x1b[38;2;255;0;0m{name}\x1b[0m'
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
            log(content)

        self.logger.publish()

        log(
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
        if (
            context.parent_expression is not None
            and not context.parent_expression.can_be_nested()
            and not container.allow_nested_expressions
            and any(
                ctx.parent_expression is not None
                and not ctx.parent_expression.can_be_nested()
                for ctx in container.contexts
            )
        ):
            raise SyntaxError(
                'It is not allowed to put another nestable expression (if/random) inside of a nestable expression.'
            )
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

    container.finalize()
    if should_disable_global_export():
        log(
            '\x1b[38;2;255;0;0mGlobal export is disabled. No .htsl file will be written.\x1b[0m'
        )
    else:
        container.export(GLOBAL_NAME)

    from .execute.decorator import run_saved_execution_contexts

    run_saved_execution_contexts()

    from .misc.sounds import SOUND_MIXER
    SOUND_MIXER.shutdown()


sys.excepthook = exception_hook
atexit.register(on_program_exit)
