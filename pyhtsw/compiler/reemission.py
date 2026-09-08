from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from pyhtsw.utils.warn import SourceSite, consumer_site, warn_at

if TYPE_CHECKING:
    from pyhtsw.expression.expression import Expression

__all__ = ('check_reemission', 'clear_emission_marks', 'suppress_reemission')

# Marks live out here rather than on the expressions: several passes walk an
# expression's own fields, and an attribute holding another expression makes
# them recurse.
_OWNER: dict[int, int] = {}
_SITE: dict[int, SourceSite | None] = {}
_ORIGIN: dict[int, int] = {}
_PINNED: list[object] = []


_SUPPRESSED: list[bool] = []


@contextmanager
def suppress_reemission() -> Generator[None]:
    """For a helper that deliberately re-emits, like `chunked` re-testing one
    condition per chunk."""
    _SUPPRESSED.append(True)
    try:
        yield
    finally:
        _SUPPRESSED.pop()


def note_clone(source: object, clone: object) -> None:
    """A clone stands in for its source: `fix_type_compatibility` coerces an
    operand into a copy, and the copy still costs the same actions."""
    origin = _ORIGIN.get(id(source), id(source))
    _ORIGIN[id(clone)] = origin
    _PINNED.append(source)
    _PINNED.append(clone)


def _key(operand: object) -> int:
    return _ORIGIN.get(id(operand), id(operand))


def _operands(expression: 'Expression') -> 'list[Expression]':
    from pyhtsw.expression.binary_expression import BinaryExpression
    from pyhtsw.expression.compound_expression import CompoundExpression
    from pyhtsw.expression.condition.comparison_condition import ComparisonCondition
    from pyhtsw.expression.condition.conditional_expression import ConditionalExpression

    found: list[Expression] = []
    for inner in expression.walk_expressions():
        if isinstance(inner, BinaryExpression | CompoundExpression):
            found.append(inner)
        if not isinstance(inner, ConditionalExpression):
            continue
        for condition in inner.conditions:
            if not isinstance(condition, ComparisonCondition):
                continue
            for side in (condition.left, condition.right):
                if isinstance(side, BinaryExpression | CompoundExpression):
                    found.extend(side.walk_expressions())
    return found


def check_reemission(statement: 'Expression') -> None:
    """Warn when a computed operand is reachable from two written statements.

    Both of them flatten it, so it costs its actions twice, which is invisible
    in the source and easy to write by accident in a guard-then-use pattern.
    """
    if _SUPPRESSED:
        return
    site: SourceSite | None = None
    looked_up = False
    owner = id(statement)
    # Only the outermost repeat is worth naming; everything under it repeats
    # for the same reason.
    covered: set[int] = set()
    for operand in _operands(statement):
        key = _key(operand)
        if key in covered:
            _OWNER[key] = owner
            continue
        previous = _OWNER.get(key)
        if previous == owner:
            continue
        if previous is None:
            if not looked_up:
                site = consumer_site()
                looked_up = True
            _OWNER[key] = owner
            _SITE[key] = site
            _PINNED.append(operand)
            continue
        first = _SITE.get(key)
        where = f' (first used at {first.filename}:{first.lineno})' if first else ''
        warn_at(
            f'{operand!r} is used by two separate statements{where}, so it is '
            f'computed twice. Assign it to a TemporaryStat once and use that, '
            f'or .cloned() it if the repeat is intended.',
            site=consumer_site(),
        )
        _OWNER[key] = owner
        covered.update(_key(inner) for inner in operand.walk_expressions())


def clear_emission_marks(expressions: 'list[Expression]') -> None:
    """Forget that these were written, so re-emitting them is not a repeat."""
    for expression in expressions:
        for operand in _operands(expression):
            _OWNER.pop(_key(operand), None)
            _SITE.pop(_key(operand), None)
