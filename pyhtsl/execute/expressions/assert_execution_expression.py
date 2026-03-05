from typing import TYPE_CHECKING, NoReturn, Self

from ...expression.condition.conditional_expression import ConditionalMode
from .execution_expression import ExecutionExpression

if TYPE_CHECKING:
    from ...expression.condition.condition import Condition
    from ..context import ExecutionContext


__all__ = ('AssertExecutionExpression',)


class AssertExecutionExpression(ExecutionExpression):
    conditions: list['Condition']
    mode: ConditionalMode
    message: str | None

    def __init__(
        self,
        conditions: list['Condition'],
        *,
        mode: ConditionalMode,
        message: str | None = None,
    ) -> None:
        self.conditions = conditions
        self.mode = mode
        self.message = message

    def cloned(self) -> Self:
        return self.__class__(
            conditions=[cond.cloned() for cond in self.conditions],
            mode=self.mode,
            message=self.message,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, AssertExecutionExpression):
            return False
        if self.mode != other.mode:
            return False
        if len(self.conditions) != len(other.conditions):
            return False
        return all(
            self.conditions[i].equals(other.conditions[i])
            for i in range(len(self.conditions))
        )

    def __repr__(self) -> str:
        return f'AssertExecutionExpression(conditions={self.conditions!r}, mode={self.mode!r})'

    def throw(
        self,
        context: 'ExecutionContext',
        *,
        false_conditions: list['Condition'],
    ) -> NoReturn:
        message = (
            f'"{context.substitute(self.message)}": ' if self.message else ''
        )
        if self.mode is ConditionalMode.AND:
            assert len(false_conditions) == 1
            middle = 'The following condition did not hold: '
        else:
            middle = 'None of the following conditions held: '
        raise AssertionError(
            f'{message}{middle}{", ".join(repr(cond) for cond in false_conditions)}'
        )

    def raw_execute(self, context: 'ExecutionContext') -> None:
        if self.mode == ConditionalMode.AND:
            for condition in self.conditions:
                if not condition.execute(context):
                    self.throw(context, false_conditions=[condition])
        elif self.mode == ConditionalMode.OR:
            for condition in self.conditions:
                if condition.execute(context):
                    return
            self.throw(context, false_conditions=self.conditions)
