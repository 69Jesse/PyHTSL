from typing import TYPE_CHECKING, NoReturn, Self

from ...expression.condition.conditional_expression import ConditionalMode
from ..exception import descriptive_backend_type
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
        return f'{self.__class__.__name__}(conditions={self.conditions!r}, mode={self.mode!r})'

    def throw(
        self,
        context: 'ExecutionContext',
        *,
        failed_conditions: list['Condition'],
    ) -> NoReturn:
        from ...checkable import Checkable

        assert len(failed_conditions) > 0

        message = (
            f'"{context.get(self.message, output="string")}": ' if self.message else ''
        )
        if self.mode is ConditionalMode.AND:
            assert len(failed_conditions) == 1
            middle = 'The following condition did not hold: '
        else:
            middle = 'None of the following conditions held: '

        def descriptive_condition(cond: 'Condition') -> str:
            return f'{" " * 4}{cond!r}\n' + '\n'.join(
                f'{" " * 8}{part!r}: {descriptive_backend_type(context.get(part, output="backend"))}'
                for part in cond.related_debug_parts()
                if isinstance(part, Checkable)
            )

        raise AssertionError(
            f'{message}{middle}\n'
            + '\n'.join(map(descriptive_condition, failed_conditions))
        )

    def raw_execute(self, context: 'ExecutionContext') -> None:
        if self.mode == ConditionalMode.AND:
            for condition in self.conditions:
                if not condition.evaluate(context):
                    self.throw(context, failed_conditions=[condition])
        elif self.mode == ConditionalMode.OR:
            for condition in self.conditions:
                if condition.evaluate(context):
                    return
            self.throw(context, failed_conditions=self.conditions)
