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
    get_project_name,
    get_projects_folder,
    should_cleanup_stale_files,
    should_disable_global_export,
    should_display_htsl,
)
from .logger import AntiSpamLogger
from .utils.kebab import into_kebab
from .utils.log import log

if TYPE_CHECKING:
    from .block import Block
    from .editable import Editable
    from .expression.expression import Expression
    from .importable import Importable, Project


__all__ = (
    'Container',
    'get_current_container',
)


WRITE_EXPRESSION_OVERRIDE_STACK: list[Callable[['Expression'], None]] = []


def _format_nested_compound_error(
    child: 'Expression',
    offender: 'Expression',
    open_expr: 'Expression',
) -> str:
    lines: list[str] = [
        'It is not allowed to write a nestable expression (if/random) inside of another nestable expression.',
        '',
        'The expression you are writing expands into a nestable block. This happens'
        ' with operations like "%" (modulo) and abs(), which compile to an if-block:',
        f'    {child!r}',
        f'    expands into:  {offender.describe_nestable_block()}',
        *(f'        {detail}' for detail in offender.nestable_block_detail_lines()),
        '',
        f'but you are still inside:  {open_expr.describe_nestable_block()}',
        *(f'    {detail}' for detail in open_expr.nestable_block_detail_lines()),
        '',
        'Compute it into a stat before the block (e.g. "tmp.value = x % 100" outside'
        ' the block, then use "tmp" inside), or restructure your conditionals.',
    ]
    return '\n'.join(lines)


@contextmanager
def override_write_expression(
    func: Callable[['Expression'], None],
) -> Generator[None]:
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
    importables: list['Importable']
    importable_keys: set[tuple[str, str]]
    project: 'Project | None'
    _reserved_temp_numbers: set[int]

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
        self.importables = []
        self.importable_keys = set()
        self.project = None
        self._reserved_temp_numbers = set()

        self.is_finalized = False
        self.allow_nested_expressions = allow_nested_expressions
        self.ignore_action_limits = ignore_action_limits

    def register_importable(self, importable: 'Importable') -> None:
        key = (importable.kind, importable.identifier())
        if key in self.importable_keys:
            raise RuntimeError(
                f'An importable of kind "{importable.kind}" named '
                f'"{importable.identifier()}" already exists. Names must be unique.',
            )
        self.importable_keys.add(key)
        self.importables.append(importable)

    def expressions(self) -> list['Expression']:
        def throw() -> NoReturn:
            raise RuntimeError(
                'Shortcut "Container.expressions" should only be used when there is exactly one non-empty block in the container'
                ', since it would be ambiguous otherwise. Use "Container.blocks" to access the blocks directly and get their expressions.',
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
        try:
            self.finalize()
        finally:
            CONTAINERS.pop()

    def _materialize_deferred(
        self,
        deferred_ids: list[int],
    ) -> tuple[list['Expression'], dict[int, str], dict[int, 'Editable']]:
        from . import deferred
        from .expression.binary_expression import BinaryExpression

        setup: list[Expression] = []
        results: list[tuple[int, Editable, bool]] = []
        for deferred_id in deferred_ids:
            entry = deferred.lookup_deferred(deferred_id)
            sub_expressions, result = entry.checkable.materialize()
            setup.extend(sub_expressions)
            results.append((deferred_id, result, entry.include_fallback_value))

        BinaryExpression.optimize_binary_expressions(setup)
        BinaryExpression.rename_temporary_stats(setup, finalize=True)

        placeholders = {
            deferred_id: result.resolved_inside_string(include_fallback_value)
            for deferred_id, result, include_fallback_value in results
        }
        editables = {deferred_id: result for deferred_id, result, _ in results}
        return setup, placeholders, editables

    def _resolve_deferred_expressions(
        self,
        expressions: list['Expression'],
    ) -> None:
        from . import deferred
        from .expression.binary_expression import BinaryExpression
        from .expression.compound_expression import CompoundExpression

        index = 0
        while index < len(expressions):
            expression = expressions[index]

            for nested in expression.nested_expressions_refs():
                self._resolve_deferred_expressions(nested)

            ids: dict[int, None] = {}
            # Computed expressions passed directly as a field (e.g. an action
            # argument) only become a sentinel when into_htsl stringifies them —
            # register them now so they share this statement's materialize batch.
            # BinaryExpression/CompoundExpression handle their own operands via
            # the flatten path, so we never materialize their fields here.
            handles_own_operands = isinstance(
                expression,
                BinaryExpression | CompoundExpression,
            )
            direct_fields: list[tuple[str, int]] = []
            for key, value in expression._get_all_values().items():
                if not handles_own_operands and isinstance(
                    value,
                    BinaryExpression | CompoundExpression,
                ):
                    deferred_id = deferred.find_deferred_ids(
                        value.into_inside_string(),
                    )[0]
                    ids.setdefault(deferred_id, None)
                    direct_fields.append((key, deferred_id))
                elif isinstance(value, str):
                    for deferred_id in deferred.find_deferred_ids(value):
                        ids.setdefault(deferred_id, None)
            if not ids:
                index += 1
                continue

            setup, placeholders, editables = self._materialize_deferred(list(ids))
            for key, value in expression._get_all_values().items():
                if isinstance(value, str) and deferred.text_has_deferred(value):
                    setattr(
                        expression,
                        key,
                        deferred.substitute_deferred(value, placeholders),
                    )
            for key, deferred_id in direct_fields:
                setattr(expression, key, editables[deferred_id])
            expressions[index:index] = setup
            index += len(setup) + 1

    def _verify_no_nested_blocks(self, expressions: list['Expression']) -> None:
        """A nestable block (if/random) must not contain another nestable, even
        one buried inside a compound expression. `%` and `abs()` expand into an
        if-block under the hood, so `x.value = x % 100` inside an `IfAll` would
        otherwise emit illegal nested conditionals."""
        if self.allow_nested_expressions:
            return
        for expression in expressions:
            nested_refs = expression.nested_expressions_refs()
            if not nested_refs:
                continue
            for body in nested_refs:
                for child in body:
                    offender = next(
                        (
                            expr
                            for expr in child.walk_expressions()
                            if not expr.can_be_nested()
                        ),
                        None,
                    )
                    if offender is not None:
                        raise SyntaxError(
                            _format_nested_compound_error(child, offender, expression),
                        )

    def _pin_held_temps(self, expressions: list['Expression']) -> None:
        """A `TemporaryStat` a consumer/helper holds across statements must keep
        one stable `tmp<n>` name for all its reads and writes. Assign it now,
        reserving it so the per-statement transient temps skip it. Transient
        flatten temps don't exist yet (created later), so the only temps visible
        here are the held ones."""
        from .stats.temporary_stat import TemporaryStat

        held: list[TemporaryStat] = []
        seen: set[object] = set()

        def visit(exprs: list['Expression']) -> None:
            for expression in exprs:
                for nested in expression.nested_expressions_refs():
                    visit(nested)
                for expr in expression.walk_expressions():
                    for stat, _ in expr.get_all_stats_used():
                        if (
                            isinstance(stat, TemporaryStat)
                            and stat._number.persistent
                            and stat._number not in seen
                        ):
                            seen.add(stat._number)
                            held.append(stat)

        visit(expressions)

        reserved = self._reserved_temp_numbers
        next_number = 0
        for stat in held:
            if stat._number.finalized:
                reserved.add(stat.number)
                continue
            while next_number in reserved:
                next_number += 1
            reserved.add(next_number)
            stat.number = next_number
            stat._number.finalized = True
            next_number += 1

    def finalize_expressions(self, expressions: list['Expression']) -> None:
        from .actions.no_optimization import no_optimization
        from .expression.binary_expression import BinaryExpression

        self._pin_held_temps(expressions)
        self._resolve_deferred_expressions(expressions)
        self._verify_no_nested_blocks(expressions)

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

    def _collect_reserved_temp_numbers(
        self,
        expressions: list['Expression'],
        numbers: set[int],
    ) -> None:
        from .checkable import Checkable
        from .stats.stat import Stat
        from .stats.temporary_stat import TemporaryStat

        def consider(stat: object) -> None:
            if isinstance(stat, Stat) and not isinstance(stat, TemporaryStat):
                n = TemporaryStat.extract_number_from_name(stat.name)
                if n is not None:
                    numbers.add(n)

        for expression in expressions:
            for nested in expression.nested_expressions_refs():
                self._collect_reserved_temp_numbers(nested, numbers)
            for expr in expression.walk_expressions():
                for stat, _ in expr.get_all_stats_used():
                    consider(stat)
                for value in expr._get_all_values().values():
                    if isinstance(value, str):
                        for ref in Checkable.iter_in_string(value):
                            consider(ref)

    def compute_reserved_temp_numbers(self) -> set[int]:
        numbers: set[int] = set()
        for block in self.blocks:
            self._collect_reserved_temp_numbers(block.expressions, numbers)
        return numbers

    def finalize(self) -> None:
        from .stats.temporary_stat import reserved_temp_numbers

        if self.is_finalized:
            raise RuntimeError('Container is already finalized')
        self._reserved_temp_numbers = self.compute_reserved_temp_numbers()
        with reserved_temp_numbers(self._reserved_temp_numbers):
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
                'Unable to transform Container into htsl: Container is not finalized. Either exit the container context or call "finalize()" manually',
            )

        with override_write_expression(lambda _: None):
            lines = (
                '\n\n\n'.join(
                    block.into_htsl() for block in self.blocks if not block.is_empty()
                )
            ).split('\n')

        self.prettify_htsl_lines(lines)
        return '\n'.join(lines)

    def project_path(self, name: str) -> Path:
        return get_projects_folder() / into_kebab(name)

    def is_empty(self) -> bool:
        return all(block.is_empty() for block in self.blocks)

    def _collect_importables(self, name: str) -> list['Importable']:
        from .importable import FunctionImportable

        importables = list(self.importables)
        global_block = self.blocks[0]
        if not global_block.is_empty():
            log(
                f'\x1b[38;2;255;191;0mActions were written outside of any importable; '
                f'wrapping them into a function named "{name}". Put them inside an '
                f'importable (e.g. @create_function) to silence this.\x1b[0m',
            )
            importables.insert(0, FunctionImportable(global_block, name=name))
        return importables

    def export(
        self,
        name: str,
        *,
        module_prefix: tuple[str, ...] | None = None,
    ) -> None:
        from .importable import Project
        from .module_export import export_project

        importables = self._collect_importables(name)
        if not importables:
            log(
                'Nothing found to export. \x1b[38;2;255;0;0mPyHTSW will not do anything.\x1b[0m',
            )
            return

        if name in self.exported_names:
            raise RuntimeError(
                f'Container with name "{name}" has already been exported.'
                + (
                    ' This is the global export, it is possible to disable the global export with "pyhtsw.disable_global_export()".'
                    if self.is_global
                    else ''
                ),
            )
        self.exported_names.add(name)

        log(
            f'\n\x1b[38;2;0;255;0mExporting {"global " * (self.is_global)}project named \x1b[38;2;255;0;0m{name}\x1b[0m',
        )

        root = self.project_path(name)
        project = Project(root)
        self.project = project
        CONTAINERS.append(self)
        try:
            export_project(project, importables, module_prefix)
        finally:
            CONTAINERS.pop()
            self.project = None

        if should_cleanup_stale_files():
            project.cleanup_stale()

        if should_display_htsl():
            for written in sorted(project.written_paths):
                rel = written.relative_to(root).as_posix()
                log(
                    f'\n\x1b[38;2;0;255;0m// {rel}\x1b[0m\n'
                    + written.read_text(encoding='utf-8'),
                )

        self.logger.publish()

        log(
            '\n\x1b[38;2;0;255;0mAll done! Your HTSW project is written to:\x1b[0m'
            f'\n{root.absolute()}'
            f'\nImport it with HTSW using the project named: \x1b[38;2;255;0;0m{name}\x1b[0m'
            '\n',
        )


def _format_nested_expression_error(
    new_context: ExpressionContext,
    open_context: ExpressionContext,
) -> str:
    assert new_context.parent_expression is not None
    assert open_context.parent_expression is not None
    new_expr = new_context.parent_expression
    open_expr = open_context.parent_expression
    # Among nestable contexts, only the `Else` branch is added with
    # `add_expression_to_container=False`.
    branch = '' if open_context.add_expression_to_container else ' (else branch)'

    lines: list[str] = [
        'It is not allowed to write a nestable expression (if/random) inside of another nestable expression.',
        '',
        f'You are trying to write:  {new_expr.describe_nestable_block()}',
        *(f'    {detail}' for detail in new_expr.nestable_block_detail_lines()),
        '',
        f'but you are still inside:  {open_expr.describe_nestable_block()}{branch}',
        *(f'    {detail}' for detail in open_expr.nestable_block_detail_lines()),
    ]

    written = open_context.expressions_ref
    if written:
        count = len(written)
        plural = '' if count == 1 else 's'
        limit = 15
        lines.append('')
        lines.append(f'{count} expression{plural} written in that block so far:')
        for index, expr in enumerate(written[:limit], start=1):
            lines.append(f'  {index}. {expr!r}')
        if count > limit:
            lines.append(f'  ... and {count - limit} more')
    return '\n'.join(lines)


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
        ):
            # A function body starts a fresh nesting scope. Entering a block
            # pushes a context with `parent_expression is None`; an if/random
            # inside that body is emitted as its own HTSL block, so if/random
            # blocks opened before the boundary must not count. Only consider
            # contexts opened after the most recent block boundary.
            boundary = -1
            for index, ctx in enumerate(container.contexts):
                if ctx.parent_expression is None:
                    boundary = index
            open_nestables = [
                ctx
                for ctx in container.contexts[boundary + 1 :]
                if ctx.parent_expression is not None
                and not ctx.parent_expression.can_be_nested()
            ]
            if open_nestables:
                raise SyntaxError(
                    _format_nested_expression_error(context, open_nestables[-1]),
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


GLOBAL_NAME = into_kebab(
    os.path.basename(sys.argv[0]).rsplit('.', 1)[0],
    default='project',
)
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
            'Program exited without exporting a non-global container. This should never happen.',
        )

    container.finalize()
    if should_disable_global_export():
        log(
            '\x1b[38;2;255;0;0mGlobal export is disabled. No .htsl file will be written.\x1b[0m',
        )
    else:
        container.export(get_project_name() or GLOBAL_NAME)

    from .execute.decorator import run_saved_execution_contexts

    run_saved_execution_contexts()

    from .misc.sounds import SOUND_MIXER

    SOUND_MIXER.shutdown()


sys.excepthook = exception_hook
atexit.register(on_program_exit)
