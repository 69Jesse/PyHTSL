import atexit
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, NamedTuple, NoReturn, Self, Unpack

from pyhtsw.compiler.settings import (
    SETTING_NAMES,
    ContainerSettings,
    PostExportHook,
    as_projects_folder,
    check_house_uuid,
    check_post_export,
    inherited_setting,
    setting,
)
from pyhtsw.config import get_projects_folder
from pyhtsw.utils.callback import call_with_optional_args
from pyhtsw.utils.kebab import into_kebab
from pyhtsw.utils.log import log
from pyhtsw.utils.warn import SourceSite, consumer_site, warn_at

if TYPE_CHECKING:
    from pyhtsw.compiler.block import Block
    from pyhtsw.compiler.importable import Importable, Project
    from pyhtsw.compiler.item_plan import ItemPlan
    from pyhtsw.compiler.limits import ImportableKind
    from pyhtsw.editable import Editable
    from pyhtsw.expression.expression import Expression


__all__ = (
    'Container',
    'get_current_container',
    'get_global_container',
    'configure',
    'disable_global_export',
)


WRITE_EXPRESSION_OVERRIDE_STACK: list[Callable[['Expression'], None]] = []

CONTAINERS: list['Container'] = []
EXPORTED_ROOTS: set[Path] = set()


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


def _overridden(explicit: bool | None, configured: bool) -> bool:
    return configured if explicit is None else explicit


class ActionLimitViolation(NamedTuple):
    name: str
    kind: 'ImportableKind'
    leftover: int


class Container:
    blocks: list['Block']
    contexts: list[ExpressionContext]
    importables: list['Importable']
    importables_by_key: dict[tuple[str, str], 'Importable']
    importables_by_unique_key: dict[tuple[str, str, str], 'Importable']
    project: 'Project | None'
    item_plan: 'ItemPlan | None'
    _consumer_reserved: set[int]
    _action_limit_violations: list['ActionLimitViolation']
    _global_site: SourceSite | None
    _settings: dict[str, Any]

    is_finalized: bool

    project_name = setting[str | None](None)
    auto_export = setting[bool](True)

    house_uuid = inherited_setting[str | None](None, transform=check_house_uuid)
    projects_folder = inherited_setting[Path | None](
        None,
        transform=as_projects_folder,
    )
    cleanup_stale_files = inherited_setting[bool](False)
    display_output = inherited_setting[bool](False)
    ignore_action_limits = inherited_setting[bool](False)
    ignore_scope = inherited_setting[bool](False)
    allow_nested_expressions = inherited_setting[bool](False)
    post_export = inherited_setting[PostExportHook | None](
        None,
        transform=check_post_export,
    )

    def __init__(self, **settings: Unpack[ContainerSettings]) -> None:
        from pyhtsw.compiler.block import GlobalBlock

        self._settings = {}
        self.blocks = []
        self.add_block(GlobalBlock())
        self.contexts = []
        self.importables = []
        self.importables_by_key = {}
        self.importables_by_unique_key = {}
        self.project = None
        self.item_plan = None
        self._consumer_reserved = set()
        self._action_limit_violations = []
        self._global_site = None

        self.is_finalized = False
        self.configure(**settings)

    def configure(self, **settings: Unpack[ContainerSettings]) -> Self:
        for name, value in settings.items():
            if name not in SETTING_NAMES:
                raise TypeError(
                    f'Unknown container setting "{name}". Valid settings are: '
                    + ', '.join(sorted(SETTING_NAMES)),
                )
            setattr(self, name, value)
        return self

    def has_importable(self, kind: str, name: str) -> bool:
        return (kind, name) in self.importables_by_key

    def find_importable(self, kind: str, name: str) -> 'Importable | None':
        return self.importables_by_key.get((kind, name))

    def report_action_limit_violation(self, block: 'Block', leftover: int) -> None:
        """Record a block that ran out of room and cannot carve out a follow-up
        function. Collected rather than raised on the spot: a house that hits
        this usually hits it in several blocks at once."""
        self._action_limit_violations.append(
            ActionLimitViolation(
                name=block.get_name(),
                kind=block.importable_kind,
                leftover=leftover,
            ),
        )

    def _raise_action_limit_violations(self) -> None:
        from pyhtsw.compiler.limits import ActionLimitError

        if not self._action_limit_violations:
            return
        # Kept, not cleared: the blocks were already rewritten in place, so a
        # second finalize has to fail the same way instead of fixing them twice.
        lines = [
            f'  - {violation.kind[:-1]} "{violation.name}": '
            f'{violation.leftover} expression(s) did not fit'
            for violation in self._action_limit_violations
        ]
        raise ActionLimitError(
            'These action lists are over the Housing limit and cannot be split '
            'automatically:\n'
            + '\n'.join(lines)
            + '\n\nOnly a function may spill into a follow-up function, because '
            'triggering one costs 4 ticks and a click handler can fire faster '
            'than that - splitting these behind your back would silently drop or '
            'reorder the tail. Move the overflowing actions into their own '
            '@function and call it (the same 4 ticks, but now visible), '
            'or shorten the list. Pass ignore_action_limits=True to the Container '
            'to skip this check.',
        )

    def _raise_scope_violations(self) -> None:
        from pyhtsw.compiler.scope import check_scopes, raise_scope_violations

        if self.ignore_scope:
            return
        raise_scope_violations(check_scopes(self.blocks, self.importables))

    def register_importable(self, importable: 'Importable') -> None:
        key = (importable.kind, importable.identifier())
        if key in self.importables_by_key:
            raise RuntimeError(
                f'An importable of kind "{importable.kind}" named '
                f'"{importable.identifier()}" already exists. Names must be unique.',
            )
        unique = importable.unique_key()
        if unique is not None:
            label, value = unique
            unique_key = (importable.kind, label, value)
            existing = self.importables_by_unique_key.get(unique_key)
            if existing is not None:
                raise RuntimeError(
                    f'An importable of kind "{importable.kind}" already uses '
                    f'{label} "{value}" (it is "{existing.identifier()}"). '
                    f'htsw rejects duplicates on this field.',
                )
            self.importables_by_unique_key[unique_key] = importable
        self.importables_by_key[key] = importable
        self.importables.append(importable)

    def rename_importable(self, importable: 'Importable', name: str) -> None:
        key = (importable.kind, name)
        if key in self.importables_by_key:
            raise RuntimeError(
                f'An importable of kind "{importable.kind}" named "{name}" '
                f'already exists. Names must be unique.',
            )
        self.importables_by_key.pop(
            (importable.kind, importable.identifier()),
            None,
        )
        importable.rename(name)
        self.importables_by_key[key] = importable

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
        return bool(CONTAINERS) and self is CONTAINERS[0]

    def get_expressions_ref_in_context(self, *, go_back: int = 0) -> list['Expression']:
        if go_back >= len(self.contexts):
            return self.blocks[0].expressions
        return self.contexts[-1 - go_back].expressions_ref

    def write_expression(self, expression: 'Expression') -> None:
        from pyhtsw.directives.preserved import currently_preserved, tag_preserved
        from pyhtsw.directives.strict_order import (
            current_strict_order_region,
            tag_strict_order_region,
        )

        if WRITE_EXPRESSION_OVERRIDE_STACK:
            WRITE_EXPRESSION_OVERRIDE_STACK[-1](expression)
            return

        if self.is_finalized:
            return

        tag_strict_order_region(expression, current_strict_order_region())
        tag_preserved(expression, currently_preserved())
        if not self.contexts and self._global_site is None:
            self._global_site = consumer_site()
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
        from pyhtsw.compiler import deferred
        from pyhtsw.expression.binary_expression import BinaryExpression

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
        from pyhtsw.compiler import deferred
        from pyhtsw.directives.strict_order import (
            strict_order_region_of,
            tag_strict_order_region,
        )
        from pyhtsw.expression.binary_expression import BinaryExpression
        from pyhtsw.expression.compound_expression import CompoundExpression
        from pyhtsw.location import Location

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
            # A location renders from its operands, so it is those that get
            # substituted -- a rendered coordinate string kept beside them would
            # be derived state going stale under the rewrite. Expanding them in
            # place keeps one loop, and the holder says where to write back.
            fields: list[tuple[object, str, object]] = []
            for key, value in expression._get_all_values().items():
                if isinstance(value, Location):
                    fields.extend(
                        (value, name, getattr(value, name))
                        for name in value.coordinate_fields()
                    )
                else:
                    fields.append((expression, key, value))

            computed_fields: list[tuple[object, str, int]] = []
            for holder, key, value in fields:
                if not handles_own_operands and isinstance(
                    value,
                    BinaryExpression | CompoundExpression,
                ):
                    deferred_id = deferred.find_deferred_ids(
                        value.into_inside_string(),
                    )[0]
                    ids.setdefault(deferred_id, None)
                    computed_fields.append((holder, key, deferred_id))
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
            for holder, key, deferred_id in computed_fields:
                setattr(holder, key, editables[deferred_id])
            # The setup belongs to the statement that reads it, so it inherits
            # its strict-order region instead of being free to drift out of one.
            region = strict_order_region_of(expression)
            for setup_expression in setup:
                tag_strict_order_region(setup_expression, region)
            expressions[index:index] = setup
            index += len(setup) + 1

    def _verify_no_nested_blocks(self, expressions: list['Expression']) -> None:
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

    def _pin_held_temps(self, expressions: list['Expression']) -> set[int]:
        from pyhtsw.compiler import deferred
        from pyhtsw.expression.expression import Expression
        from pyhtsw.location import Location
        from pyhtsw.stats.temporary_stat import Number, TemporaryStat

        first: dict[Number, int] = {}
        last: dict[Number, int] = {}
        counter = 0

        def mark(stat: object, idx: int) -> None:
            if isinstance(stat, TemporaryStat) and stat._number.persistent:
                num = stat._number
                if num not in first:
                    first[num] = idx
                last[num] = idx

        def mark_deferred(checkable: object, idx: int) -> None:
            if isinstance(checkable, Expression):
                for expr in checkable.walk_expressions():
                    for stat, _ in expr.get_all_stats_used():
                        mark(stat, idx)
            else:
                mark(checkable, idx)

        def visit(exprs: list['Expression']) -> None:
            nonlocal counter
            for expression in exprs:
                idx = counter
                counter += 1
                for expr in expression.walk_expressions():
                    for stat, _ in expr.get_all_stats_used():
                        mark(stat, idx)
                    for value in expr._get_all_values().values():
                        if isinstance(value, str):
                            for did in deferred.find_deferred_ids(value):
                                mark_deferred(
                                    deferred.lookup_deferred(did).checkable,
                                    idx,
                                )
                        elif isinstance(value, Location):
                            for stat in value.iter_referenced_stats():
                                mark(stat, idx)
                for nested in expression.nested_expressions_refs():
                    visit(nested)

        visit(expressions)

        consumer = self._consumer_reserved
        fixed = {num.value for num in first if num.finalized}
        base_reserved = consumer | fixed

        order = sorted(
            (num for num in first if not num.finalized),
            key=lambda n: first[n],
        )
        active: list[tuple[int, int]] = []  # (last_index, number) still live
        assigned: set[int] = set(fixed)
        for num in order:
            start = first[num]
            active = [(end, n) for (end, n) in active if end >= start]
            live = {n for (_, n) in active} | base_reserved
            number = 0
            while number in live:
                number += 1
            num.value = number
            num.finalized = True
            active.append((last[num], number))
            assigned.add(number)
        return consumer | assigned

    def finalize_expressions(self, expressions: list['Expression']) -> set[int]:
        """Finalize one block's expressions. Returns the block's reserved temp
        numbers (consumer names + this block's held temps) so the caller can
        activate the same set while rendering/executing the block."""
        from pyhtsw.directives.no_optimization import optimization_enabled
        from pyhtsw.expression.binary_expression import BinaryExpression
        from pyhtsw.stats.temporary_stat import reserved_temp_numbers

        block_reserved = self._pin_held_temps(expressions)
        with reserved_temp_numbers(block_reserved):
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

            BinaryExpression.optimize_binary_expressions(expressions)
            if optimization_enabled('reorder'):
                self._reorder_for_folding(expressions)
        return block_reserved

    @staticmethod
    def _reorder_for_folding(expressions: list['Expression']) -> None:
        from pyhtsw.compiler.limits import total_action_count
        from pyhtsw.compiler.schedule import reorder_for_folding
        from pyhtsw.expression.binary_expression import BinaryExpression

        candidate = reorder_for_folding(expressions)
        if candidate is None:
            return
        trial = [expression.cloned() for expression in candidate]
        BinaryExpression.optimize_binary_expressions(trial)
        if total_action_count(trial) >= total_action_count(expressions):
            return
        expressions[:] = candidate
        BinaryExpression.optimize_binary_expressions(expressions)

    def _collect_reserved_temp_numbers(
        self,
        expressions: list['Expression'],
        numbers: set[int],
    ) -> None:
        from pyhtsw.checkable import Checkable
        from pyhtsw.location import Location
        from pyhtsw.stats.stat import Stat
        from pyhtsw.stats.temporary_stat import TemporaryStat

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
                    elif isinstance(value, Location):
                        for ref in value.iter_referenced_stats():
                            consider(ref)

    def compute_reserved_temp_numbers(self) -> set[int]:
        numbers: set[int] = set()
        for block in self.blocks:
            self._collect_reserved_temp_numbers(block.expressions, numbers)
        return numbers

    def finalize(self) -> None:
        from pyhtsw.compiler.item_plan import plan_items

        if self.is_finalized:
            raise RuntimeError('Container is already finalized')
        self._wrap_global_block()
        self._raise_action_limit_violations()
        self._consumer_reserved = self.compute_reserved_temp_numbers()
        for index, block in enumerate(self.blocks):
            block.finalize(self, index)
        self._raise_action_limit_violations()
        self._raise_scope_violations()
        # Last: overflow functions carved out above own expressions too, and
        # every item has to be named before anything renders one.
        self.item_plan = plan_items(self.blocks, self.importables)
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
        folder = self.projects_folder
        if folder is None:
            folder = get_projects_folder()
        return folder / into_kebab(name)

    def is_empty(self) -> bool:
        return all(block.is_empty() for block in self.blocks)

    def _wrap_global_block(self) -> None:
        from pyhtsw.compiler.importable import FunctionImportable

        global_block = self.blocks[0]
        if global_block.is_empty():
            return
        name = global_block.get_name()
        existing = self.find_importable('functions', name)
        if isinstance(existing, FunctionImportable) and existing.block is global_block:
            return
        warn_at(
            f'Actions were written outside of any importable; wrapping them into '
            f'a function named "{name}". Put them inside an importable '
            f'(e.g. @function) to silence this.',
            self._global_site,
        )
        self.register_importable(FunctionImportable(global_block, name=name))

    def resolve_project_name(self, name: str | None = None) -> str:
        """One name-resolution rule for both the explicit and the exit-hook
        export: what was asked for, then the container's own name, then the
        script filename."""
        return name or self.project_name or GLOBAL_NAME

    def export(
        self,
        name: str | None = None,
        *,
        module_prefix: tuple[str, ...] | None = None,
        house_uuid: str | None = None,
        cleanup_stale_files: bool | None = None,
        display_output: bool | None = None,
    ) -> None:
        from pyhtsw.compiler.importable import Project
        from pyhtsw.compiler.item_plan import plan_items
        from pyhtsw.compiler.module_export import export_project

        name = self.resolve_project_name(name)

        if not self.is_finalized:
            raise RuntimeError(
                'Unable to export Container: Container is not finalized, so '
                'every block is still empty. Either exit the container context '
                'or call "finalize()" manually.',
            )
        importables = list(self.importables)
        # Replanned here rather than reusing finalize's: which module owns an
        # item decides where its .snbt is written, and a module may still be
        # (re)assigned between finalize and export. Naming is content-determined,
        # so the names themselves come out the same either way.
        self.item_plan = plan_items(self.blocks, importables)
        if not importables:
            log(
                'Nothing found to export. \x1b[38;2;255;0;0mPyHTSW will not do anything.\x1b[0m',
            )
            return

        root = self.project_path(name)
        if root in EXPORTED_ROOTS:
            raise RuntimeError(
                f'A project has already been exported to "{root}" this run.'
                + (
                    ' This is the global export, it is possible to disable the global export with "pyhtsw.disable_global_export()".'
                    if self.is_global
                    else ''
                ),
            )
        EXPORTED_ROOTS.add(root)

        log(
            f'\n\x1b[38;2;0;255;0mExporting {"global " * (self.is_global)}project named \x1b[38;2;255;0;0m{name}\x1b[0m',
        )

        project = Project(root, self.item_plan)
        self.project = project
        CONTAINERS.append(self)
        try:
            export_project(
                project,
                importables,
                module_prefix,
                house_uuid if house_uuid is not None else self.house_uuid,
            )
        finally:
            CONTAINERS.pop()
            self.project = None

        if _overridden(cleanup_stale_files, self.cleanup_stale_files):
            project.cleanup_stale()

        if _overridden(display_output, self.display_output):
            for written in sorted(project.written_paths):
                rel = written.relative_to(root).as_posix()
                log(
                    f'\n\x1b[38;2;0;255;0m// {rel}\x1b[0m\n'
                    + written.read_text(encoding='utf-8'),
                )

        log(
            '\n\x1b[38;2;0;255;0mAll done! Your HTSW project is written to:\x1b[0m'
            f'\n{root.absolute()}'
            f'\nImport it with HTSW using the project named: \x1b[38;2;255;0;0m{name}\x1b[0m'
            '\n',
        )

        hook = self.post_export
        if hook is not None:
            call_with_optional_args(hook, root, self, noun='post_export hook')


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
            for index, house in enumerate(container.contexts):
                if house.parent_expression is None:
                    boundary = index
            open_nestables = [
                house
                for house in container.contexts[boundary + 1 :]
                if house.parent_expression is not None
                and not house.parent_expression.can_be_nested()
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
CONTAINERS.append(Container())


def get_current_container() -> Container:
    return CONTAINERS[-1]


def get_global_container() -> Container:
    """The container everything written outside an explicit `with Container():`
    lands in, and the one every other container reads its unset settings from."""
    return CONTAINERS[0]


def configure(**settings: Unpack[ContainerSettings]) -> Container:
    """Configure the global container: what a script written outside an explicit
    `with Container():` exports, and what every other container inherits from."""
    return get_global_container().configure(**settings)


def disable_global_export(value: bool = True) -> None:
    """Stop the exit hook from writing the global container's project."""
    get_global_container().auto_export = not value


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
    _export_global_container()

    from pyhtsw.execute.decorator import run_saved_emulations

    run_saved_emulations()

    sounds = sys.modules.get('pyhtsw.misc.sounds')
    if sounds is not None:
        sounds.SOUND_MIXER.shutdown()


def _export_global_container() -> None:
    container = get_current_container()
    if not container.is_global:
        raise RuntimeError(
            'Program exited without exporting a non-global container. This should never happen.',
        )

    if not container.is_finalized:
        container.finalize()
    if not container.auto_export:
        log(
            '\x1b[38;2;255;0;0mGlobal export is disabled. No .htsl file will be written.\x1b[0m',
        )
    else:
        container.export()


sys.excepthook = exception_hook
atexit.register(on_program_exit)
