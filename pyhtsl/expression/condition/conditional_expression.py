from collections.abc import Generator
from enum import Enum
from typing import TYPE_CHECKING, Self, final

from ...config import INDENT
from ..expression import Expression

if TYPE_CHECKING:
    from .condition import Condition


__all__ = ('ConditionalExpression',)


class ConditionalMode(Enum):
    AND = 'and'
    OR = 'or'


@final
class ConditionalExpression(Expression):
    conditions: list['Condition']
    mode: ConditionalMode

    if_expressions: list[Expression]
    else_expressions: list[Expression]

    def __init__(
        self,
        conditions: list['Condition'],
        mode: ConditionalMode,
        *,
        if_expressions: list[Expression] | None = None,
        else_expressions: list[Expression] | None = None,
    ) -> None:
        self.conditions = conditions
        self.mode = mode
        self.if_expressions = if_expressions or []
        self.else_expressions = else_expressions or []

    def into_htsl(self) -> str:
        result = f'if {self.mode.value} ({", ".join(cond.into_htsl() for cond in self.conditions)}) {{'
        for expr in self.if_expressions:
            result += ('\n' + expr.into_htsl()).replace('\n', '\n' + INDENT)

        if not self.else_expressions:
            result += '\n}'
            return result

        result += '\n} else {'
        for expr in self.else_expressions:
            result += ('\n' + expr.into_htsl()).replace('\n', '\n' + INDENT)
        result += '\n}'

        return result

    def cloned(self) -> Self:
        return self.__class__(
            conditions=[cond.cloned() for cond in self.conditions],
            mode=self.mode,
            if_expressions=[expr.cloned() for expr in self.if_expressions],
            else_expressions=[expr.cloned() for expr in self.else_expressions],
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, ConditionalExpression):
            return False
        return (
            len(self.conditions) == len(other.conditions)
            and all(
                cond.equals(other_cond)
                for cond, other_cond in zip(
                    self.conditions,
                    other.conditions,
                    strict=False,
                )
            )
            and self.mode == other.mode
            and len(self.if_expressions) == len(other.if_expressions)
            and all(
                expr.equals(other_expr)
                for expr, other_expr in zip(
                    self.if_expressions,
                    other.if_expressions,
                    strict=False,
                )
            )
            and len(self.else_expressions) == len(other.else_expressions)
            and all(
                expr.equals(other_expr)
                for expr, other_expr in zip(
                    self.else_expressions,
                    other.else_expressions,
                    strict=False,
                )
            )
        )

    def walk_expressions(self) -> Generator[Expression, None, None]:
        yield from super().walk_expressions()
        for expr in self.if_expressions:
            yield from expr.walk_expressions()
        for expr in self.else_expressions:
            yield from expr.walk_expressions()

    def __repr__(self) -> str:
        return f'If<{self.mode.name}, conditions={len(self.conditions)}, if_exprs={len(self.if_expressions)}, else_exprs={len(self.else_expressions)}>'
