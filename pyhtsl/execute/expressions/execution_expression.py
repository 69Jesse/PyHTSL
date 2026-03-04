from typing import TYPE_CHECKING, Self

from ...expression.expression import Expression

if TYPE_CHECKING:
    from ..context import ExecutionContext


__all__ = ('ExecutionExpression',)


class ExecutionExpression(Expression):
    def into_htsl(self) -> str:
        return f'// {self!r}'
