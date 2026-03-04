import os
from collections.abc import Callable
from types import TracebackType
from typing import TYPE_CHECKING, Literal, overload

from pyhtsl.checkable import Checkable
from pyhtsl.expression.housing_type import HousingType

from ..container import Container
from ..expression.condition.conditional_expression import ConditionalMode
from ..expression.expression import Expression
from ..placeholders import DEFINED_PLACEHOLDERS
from .backend_type import (
    BackendType,
    backend_into_string,
    into_backend_type,
    into_housing_type,
)
from .expressions.assert_execution_expression import AssertExecutionExpression
from .expressions.print_execution_expression import PrintExecutionExpression

if TYPE_CHECKING:
    from ..expression.condition.condition import Condition


__all__ = ('ExecutionContext',)


class ExecutionContext(Container):
    verbose: bool
    expression_callback: Callable[[Expression], None] | None
    started_execution: bool
    checkable_mapping: dict[tuple[object, ...], BackendType]

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

    @overload
    def get(
        self,
        key: Checkable,
        *,
        default: HousingType | BackendType = ...,
        internal: bool = ...,
        enforce_string: Literal[True],
    ) -> str: ...

    @overload
    def get(
        self,
        key: Checkable,
        *,
        default: HousingType | BackendType = ...,
        internal: Literal[True],
        enforce_string: Literal[False] = ...,
    ) -> BackendType: ...

    @overload
    def get(
        self,
        key: Checkable,
        *,
        default: HousingType | BackendType = ...,
        internal: Literal[False] = ...,
        enforce_string: Literal[False] = ...,
    ) -> HousingType: ...

    def get(
        self,
        key: Checkable,
        *,
        default: HousingType | BackendType = '',
        internal: bool = False,
        enforce_string: bool = False,
    ) -> HousingType | BackendType:
        value = self.checkable_mapping.get(
            key.into_hashable(),
            into_backend_type(default),
        )
        if enforce_string:
            return backend_into_string(value)
        if internal:
            return value
        return into_housing_type(value)

    def put(
        self,
        key: Checkable,
        value: HousingType | BackendType,
    ) -> None:
        self.checkable_mapping[key.into_hashable()] = into_backend_type(value)

    def replace_placeholders(self, text: str) -> str:
        for key, value in DEFINED_PLACEHOLDERS.items():
            text = text.replace(key, self.get(value, enforce_string=True))
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
