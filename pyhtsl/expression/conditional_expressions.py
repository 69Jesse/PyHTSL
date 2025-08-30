from ..checkable import Checkable
from .housing_type import HousingType
from ..condition.conditional_statements import IfStatement
from .expression import Expression
from ..line_type import LineType
from ..writer import WRITER
from .handler import ExpressionHandler

from typing import final


__all__ = (
    'ConditionalEnterExpression',
    'ConditionalExitExpression',
)


@final
class ConditionalEnterExpression(Expression):
    statement: IfStatement

    def __init__(
        self,
        statement: IfStatement,
    ) -> None:
        self.statement = statement

    def _in_assignment_left_side(self) -> str:
        raise RuntimeError('This should not be called')

    def _in_assignment_right_side(self) -> str:
        raise RuntimeError('This should not be called')

    def _in_comparison_left_side(self) -> str:
        raise RuntimeError('This should not be called')

    def _in_comparison_right_side(self) -> str:
        raise RuntimeError('This should not be called')

    def _as_string(self, include_fallback_value: bool = True) -> str:
        raise RuntimeError('This should not be called')

    def _equals(self, other: Checkable | HousingType) -> bool:
        if not isinstance(other, ConditionalEnterExpression):
            return False
        return self.statement == other.statement

    def _copied(self) -> 'ConditionalEnterExpression':
        return ConditionalEnterExpression(
            self.statement,
        )

    def _write_line(self) -> tuple[str, LineType]:
        return self.statement._enter_line()

    def _after_write_line(self) -> None:
        WRITER.begin_indent()

    def __repr__(self) -> str:
        return f'IfEnter<{repr(self.statement)}>'


@final
class ConditionalExitExpression(Expression):
    statement: IfStatement

    def __init__(
        self,
        statement: IfStatement,
    ) -> None:
        self.statement = statement

    def _in_assignment_left_side(self) -> str:
        raise RuntimeError('This should not be called')

    def _in_assignment_right_side(self) -> str:
        raise RuntimeError('This should not be called')

    def _in_comparison_left_side(self) -> str:
        raise RuntimeError('This should not be called')

    def _in_comparison_right_side(self) -> str:
        raise RuntimeError('This should not be called')

    def _as_string(self, include_fallback_value: bool = True) -> str:
        raise RuntimeError('This should not be called')

    def _equals(self, other: Checkable | HousingType) -> bool:
        if not isinstance(other, ConditionalEnterExpression):
            return False
        return self.statement == other.statement

    def _copied(self) -> 'ConditionalEnterExpression':
        return ConditionalEnterExpression(
            self.statement,
        )

    def _before_write_line(self) -> None:
        WRITER.end_indent()

    def _write_line(self) -> tuple[str, LineType]:
        return self.statement._exit_line()

    def __repr__(self) -> str:
        return 'IfExit'


Checkable._import_conditional_expressions(
    ConditionalEnterExpression,
    ConditionalExitExpression,
)
ExpressionHandler._import_conditional_expressions(
    ConditionalEnterExpression,
    ConditionalExitExpression,
)
