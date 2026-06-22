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
        self.internal_type = result.internal_type

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
                self.expressions,
                other.expressions,
                strict=False,
            )
        )

    def _flattened_expressions(self) -> list[Expression]:
        """Clone the stored expressions, flattening any unflattened BinaryExpressions."""
        from .binary_expression import BinaryExpression

        expressions: list[Expression] = []
        for expr in self.expressions:
            expr = expr.cloned()
            if isinstance(expr, BinaryExpression):
                expressions.extend(expr.flatten())
            else:
                expressions.append(expr)
        return expressions

    def into_executable_expressions(self) -> Generator[Expression]:
        from .binary_expression import BinaryExpression

        expressions = self._flattened_expressions()
        BinaryExpression.optimize_binary_expressions(expressions)
        BinaryExpression.rename_temporary_stats(expressions)
        yield from expressions

    def write_and_get_result(self) -> Editable:
        from .binary_expression import BinaryExpression

        expressions = self._flattened_expressions()
        BinaryExpression.optimize_binary_expressions(expressions)
        # Finalized: each lands in the block as its own statement and gets
        # re-rendered independently, so the numbers must not drift.
        BinaryExpression.rename_temporary_stats(expressions, finalize=True)
        for expr in expressions:
            expr.write()
        return self.result

    def materialize(self) -> tuple[list[Expression], Editable]:
        return self._flattened_expressions(), self.result.cloned()

    def into_string_lhs(self) -> str:
        return self.write_and_get_result().into_string_lhs()

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        return self.write_and_get_result().into_string_rhs(
            include_internal_type=include_internal_type,
        )

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        from ..deferred import register_deferred

        return register_deferred(self, include_fallback_value)

    def into_htsl(self) -> str:
        from .binary_expression import BinaryExpression

        expressions = self._flattened_expressions()
        BinaryExpression.optimize_binary_expressions(expressions)
        # Finalized so the per-expression re-render below stays consistent.
        BinaryExpression.rename_temporary_stats(expressions, finalize=True)
        return '\n'.join(expr.into_htsl() for expr in expressions)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{", ".join(repr(expr) for expr in self.expressions)}>'

    def walk_expressions(self) -> Generator[Expression]:
        yield from super().walk_expressions()
        for expr in self.expressions:
            yield from expr.walk_expressions()
