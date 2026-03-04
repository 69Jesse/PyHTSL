
from ...expression.expression import Expression

__all__ = ('ExecutionExpression',)


class ExecutionExpression(Expression):
    def into_htsl(self) -> str:
        return f'// {self!r}'
