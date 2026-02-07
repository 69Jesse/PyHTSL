from ..editable import Editable
from .expression import Expression

from typing import Self, final


@final
class CompoundExpression[T: Expression](Expression, Editable):
    expressions: list[T]

    def __init__(self, expressions: list[T]) -> None:
        self.expressions = expressions

    def cloned_raw(self) -> Self:
        return self.__class__([expr.cloned() for expr in self.expressions])

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, CompoundExpression):
            return False
        return all(
            expr.equals(other_expr)
            for expr, other_expr in zip(self.expressions, other.expressions)
        )

    def into_htsl(self) -> str:
        return '\n'.join(expr.into_htsl() for expr in self.expressions)

    def execute(self) -> Self:
        for expr in self.expressions:
            expr.execute()
        return self

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{", ".join(repr(expr) for expr in self.expressions)}>'
