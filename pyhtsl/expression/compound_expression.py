from collections.abc import Generator
from typing import Self, final

from ..editable import Editable
from .expression import Expression


@final
class CompoundExpression(Expression, Editable):
    expressions: list[Expression]
    result: Editable

    def __init__(self, expressions: list[Expression], result: Editable) -> None:
        super().__init__()
        self.expressions = expressions
        self.result = result

    def cloned_raw(self) -> Self:
        return self.__class__(
            [expr.cloned() for expr in self.expressions],
            self.result.cloned(),
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, CompoundExpression):
            return False
        return all(
            expr.equals(other_expr)
            for expr, other_expr in zip(
                self.expressions, other.expressions, strict=False
            )
        )

    def into_executable_expressions(self) -> Generator[Expression, None, None]:
        from .binary_expression import BinaryExpression

        expressions = [expr.cloned() for expr in self.expressions]
        BinaryExpression.optimize_binary_expressions(expressions)  # pyright: ignore[reportArgumentType]
        BinaryExpression.rename_temporary_stats(expressions)
        yield from expressions

    def write_and_get_result(self) -> Editable:
        expressions = list(self.into_executable_expressions())
        for expr in expressions:
            expr.write()
        return self.result

    def into_string_lhs(self) -> str:
        return self.write_and_get_result().into_string_lhs()

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        return self.write_and_get_result().into_string_rhs(
            include_internal_type=include_internal_type,
        )

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        return self.write_and_get_result().into_inside_string(
            include_fallback_value=include_fallback_value,
        )

    def into_htsl(self) -> str:
        return '\n'.join(expr.into_htsl() for expr in self.expressions)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{", ".join(repr(expr) for expr in self.expressions)}>'

    def walk_expressions(self) -> Generator[Expression, None, None]:
        yield from super().walk_expressions()
        for expr in self.expressions:
            yield from expr.walk_expressions()
