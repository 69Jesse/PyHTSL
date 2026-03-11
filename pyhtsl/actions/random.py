from collections.abc import Generator
from typing import Self, final

from ..config import INDENT
from ..container import ContainerContextManager, ExpressionContext
from ..expression.expression import Expression

__all__ = ('Random',)


@final
class RandomExpression(Expression):
    expressions: list[Expression]

    def __init__(
        self,
        *,
        expressions: list[Expression] | None = None,
    ) -> None:
        self.expressions = expressions or []

    def into_htsl(self) -> str:
        result = 'random {'
        for expr in self.expressions:
            result += ('\n' + expr.into_htsl()).replace('\n', '\n' + INDENT)
        result += '\n}'
        return result

    def cloned(self) -> Self:
        return self.__class__(
            expressions=[expr.cloned() for expr in self.expressions],
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, RandomExpression):
            return False
        return len(self.expressions) == len(other.expressions) and all(
            expr.equals(other_expr)
            for expr, other_expr in zip(
                self.expressions,
                other.expressions,
                strict=False,
            )
        )

    def walk_expressions(self) -> Generator[Expression, None, None]:
        yield from super().walk_expressions()
        for expr in self.expressions:
            yield from expr.walk_expressions()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<exprs={len(self.expressions)}>'


@final
class RandomContextManager(ContainerContextManager):
    expression: RandomExpression

    def __init__(self) -> None:
        self.expression = RandomExpression()

    def create_context(self) -> ExpressionContext:
        self.expression = RandomExpression()
        return ExpressionContext(
            parent_expression=self.expression,
            expressions_ref=self.expression.expressions,
        )


Random = RandomContextManager()
