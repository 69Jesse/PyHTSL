import os
from collections.abc import Callable
from types import TracebackType
from typing import TYPE_CHECKING, NoReturn, Self

import numpy as np

from pyhtsl.checkable import Checkable
from pyhtsl.expression.housing_type import HousingType

from .container import Container
from .expression.condition.conditional_expression import ConditionalMode
from .expression.expression import Expression
from .placeholders import DEFINED_PLACEHOLDERS

if TYPE_CHECKING:
    from .expression.condition.condition import Condition
    from .expression.expression import Expression


__all__ = ('ExecutionContext',)


type InternalHousingType = np.int64 | np.float64 | str


class ExecutionContext(Container):
    verbose: bool
    expression_callback: Callable[[Expression], None] | None
    started_execution: bool
    checkable_mapping: dict[Checkable, InternalHousingType]

    def __init__(
        self,
        *,
        verbose: bool = False,
        expression_callback: Callable[[Expression], None] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name or f'ExecutionContext-{os.urandom(4).hex()}')
        self.verbose = verbose
        self.expression_callback = expression_callback
        self.started_execution = False
        self.checkable_mapping = {}

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        self.started_execution = True
        for expression in self.expressions:
            for expr in expression.into_executable_expressions():
                expr.execute(self)

    def get(
        self,
        key: Checkable,
        *,
        internal: bool = False,
        enforce_string: bool = False,
    ) -> HousingType:
        return 123

    def replace_placeholders(self, text: str) -> str:
        for key, value in DEFINED_PLACEHOLDERS.items():
            text = text.replace(f'{{{key}}}', self.get(value, enforce_string=True))
        # TODO
        return text

    def write_or_execute(self, expression: Expression) -> None:
        if self.started_execution:
            expression.execute(self)
        else:
            self.write_expression(expression)

    def print(self, *lines: object) -> None:
        self.write_or_execute(
            PrintExecutionExpression(
                line=' '.join(map(str, lines)),
            )
        )

    def assert_all(self, *conditions: 'Condition', message: object = None) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                list(conditions),
                mode=ConditionalMode.AND,
                message=str(message) if message is not None else None,
            )
        )

    def assert_any(self, *conditions: 'Condition', message: object = None) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                list(conditions),
                mode=ConditionalMode.OR,
                message=str(message) if message is not None else None,
            )
        )


class ExecutionExpression(Expression):
    def into_htsl(self) -> str:
        return f'// {self!r}'


class PrintExecutionExpression(ExecutionExpression):
    line: str

    def __init__(self, line: str) -> None:
        self.line = line

    def cloned(self) -> Self:
        return self.__class__(line=self.line)

    def equals(self, other: object) -> bool:
        if not isinstance(other, PrintExecutionExpression):
            return False
        return self.line == other.line

    def __repr__(self) -> str:
        return f'PrintExecutionExpression(line={self.line!r})'

    def raw_execute(self, context: ExecutionContext) -> None:
        print(context.replace_placeholders(self.line))


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
        context: ExecutionContext,
        *,
        false_conditions: list['Condition'],
    ) -> NoReturn:
        message = (
            f'"{context.replace_placeholders(self.message)}": ' if self.message else ''
        )
        if self.mode is ConditionalMode.AND:
            assert len(false_conditions) == 1
            middle = 'The following condition did not hold: '
        else:
            middle = 'None of the following conditions held: '
        raise AssertionError(
            f'{message}{middle}{", ".join(repr(cond) for cond in false_conditions)}'
        )

    def raw_execute(self, context: ExecutionContext) -> None:
        if self.mode == ConditionalMode.AND:
            for condition in self.conditions:
                if not condition.execute(context):
                    self.throw(context, false_conditions=[condition])
        elif self.mode == ConditionalMode.OR:
            for condition in self.conditions:
                if condition.execute(context):
                    return
            self.throw(context, false_conditions=self.conditions)
