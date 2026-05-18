from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from .actions.conditional.context_manager import (
    ElseContextManager,
    IfContextManager,
)
from .container import get_current_container, override_write_expression
from .expression.condition.conditional_expression import ConditionalExpression
from .limits import Counter

if TYPE_CHECKING:
    from .expression.expression import Expression


__all__ = ('chunk_expressions', 'chunked')


def chunk_expressions(expressions: list['Expression']) -> list[list['Expression']]:
    """Split a list of expressions into consecutive chunks that each fit within action limits."""
    chunks: list[list[Expression]] = []
    current: list[Expression] = []
    counter = Counter()
    for expression in expressions:
        if current and counter.would_exceed(expression):
            chunks.append(current)
            current = []
            counter = Counter()
        counter.increment(expression)
        current.append(expression)
    if current:
        chunks.append(current)
    return chunks


def _assert_flat(expressions: list['Expression']) -> None:
    for expression in expressions:
        if not expression.can_be_nested():
            raise SyntaxError('chunked body may not open a nested if/random block')


def _same_branch(a: ConditionalExpression, b: ConditionalExpression) -> bool:
    """Whether two conditionals guard on the same condition (ignoring bodies)."""
    return (
        a.mode == b.mode
        and len(a.conditions) == len(b.conditions)
        and all(x.equals(y) for x, y in zip(a.conditions, b.conditions, strict=True))
    )


def _fill_else_chunks(chunks: list[list['Expression']]) -> None:
    container = get_current_container()
    context = container.get_expressions_ref_in_context()

    # The preceding `chunked(IfAll(...))` left a run of same-condition `if`
    # blocks at the tail of the context, none with an `else` yet.
    group: list[ConditionalExpression] = []
    for block in reversed(context):
        if not isinstance(block, ConditionalExpression) or block.else_expressions:
            break
        if group and not _same_branch(block, group[-1]):
            break
        group.insert(0, block)
    if not group:
        raise SyntaxError('chunked(Else) has no preceding chunked if to pair with')

    for block, chunk in zip(group, chunks, strict=False):
        block.else_expressions = chunk
    # Anything past the existing blocks needs its own block: an empty `if`
    # carrying just the `else` chunk, under the same condition.
    template = group[-1]
    for chunk in chunks[len(group) :]:
        container.write_expression(
            ConditionalExpression(
                [condition.cloned() for condition in template.conditions],
                template.mode,
                else_expressions=chunk,
            )
        )


@contextmanager
def chunked(
    block: IfContextManager | ElseContextManager,
) -> Generator[None, None, None]:
    """Re-emit the `with` body across as many blocks as necessary to not exceed action limits.
    Make sure the expressions in the body do not modify whether or not the block's conditions are met.
    """
    captured: list[Expression] = []
    with override_write_expression(captured.append):
        yield
    _assert_flat(captured)
    chunks = chunk_expressions(captured)

    if isinstance(block, ElseContextManager):
        _fill_else_chunks(chunks)
    else:
        container = get_current_container()
        for chunk in chunks:
            with block.cloned():
                for expression in chunk:
                    container.write_expression(expression)
