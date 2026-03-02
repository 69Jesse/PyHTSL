from collections.abc import Generator
from typing import Self, final

from ..editable import Editable
from .expression import Expression


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
            for expr, other_expr in zip(
                self.expressions, other.expressions, strict=False
            )
        )

    def into_htsl(self) -> str:
        return '\n'.join(expr.into_htsl() for expr in self.expressions)

    def write(self) -> Self:
        for expr in self.expressions:
            expr.write()
        return self

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{", ".join(repr(expr) for expr in self.expressions)}>'

    def walk_expressions(self) -> Generator[Expression, None, None]:
        yield from super().walk_expressions()
        for expr in self.expressions:
            yield from expr.walk_expressions()
