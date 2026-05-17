from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from .container import get_current_container, override_write_expression
from .limits import Counter

if TYPE_CHECKING:
    from .actions.conditional.context_manager import IfContextManager
    from .expression.expression import Expression


__all__ = ('chunk_expressions', 'chunked_if')


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


@contextmanager
def chunked_if(if_block: 'IfContextManager') -> Generator[None, None, None]:
    captured: list[Expression] = []
    with override_write_expression(captured.append):
        yield
    for expression in captured:
        if not expression.can_be_nested():
            raise SyntaxError(
                'chunked_if body may not open a nested if/random block'
            )
    container = get_current_container()
    for chunk in chunk_expressions(captured):
        with if_block.cloned():
            for expression in chunk:
                container.write_expression(expression)
