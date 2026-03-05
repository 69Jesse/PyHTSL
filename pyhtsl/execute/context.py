import os
from collections.abc import Callable
from types import TracebackType
from typing import TYPE_CHECKING, Literal, overload

from ..container import Container
from ..expression.condition.conditional_expression import ConditionalMode
from ..expression.expression import Expression
from ..expression.housing_type import HousingType
from ..placeholders import DEFINED_PLACEHOLDERS
from .backend_type import (
    BackendType,
    backend_into_string,
    cast_to_backend_double,
    cast_to_backend_long,
    into_backend_type,
    into_housing_type,
)
from .expressions.assert_execution_expression import AssertExecutionExpression
from .expressions.print_execution_expression import PrintExecutionExpression

if TYPE_CHECKING:
    from ..checkable import Checkable
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
        self.checkable_mapping = {
            placeholder.into_hashable(): into_backend_type(
                placeholder.default_backend_value
            )
            for placeholder in DEFINED_PLACEHOLDERS.values()
        }

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
        key: 'Checkable',
        *,
        default: HousingType | BackendType = ...,
        output: Literal['regular'] = ...,
    ) -> HousingType: ...

    @overload
    def get(
        self,
        key: 'Checkable',
        *,
        default: HousingType | BackendType = ...,
        output: Literal['backend'],
    ) -> BackendType: ...

    @overload
    def get(
        self,
        key: 'Checkable',
        *,
        default: HousingType | BackendType = ...,
        output: Literal['string'],
    ) -> str: ...

    def get(
        self,
        key: 'Checkable',
        *,
        default: HousingType | BackendType = '',
        output: Literal['regular', 'backend', 'string'] = 'regular',
    ) -> HousingType | BackendType | str:
        value = self.checkable_mapping.get(
            key.into_hashable(),
            None,
        )
        if value is None:
            value = into_backend_type(default)

        if output == 'string':
            return backend_into_string(value)
        if output == 'backend':
            return value
        return into_housing_type(value)

    def _substitute_single_placeholder(self, placeholder: str) -> BackendType | None:
        for key, value in DEFINED_PLACEHOLDERS.items():
            if placeholder == key:
                return self.get(value, output='backend')
        return None

    def _substitute_all_placeholders(self, text: str) -> str:
        for key, value in DEFINED_PLACEHOLDERS.items():
            text = text.replace(key, self.get(value, output='string'))
        return text

    @overload
    def substitute(
        self,
        text: str,
        *,
        output: Literal['regular'],
    ) -> HousingType: ...

    @overload
    def substitute(
        self,
        text: str,
        *,
        output: Literal['backend'],
    ) -> BackendType: ...

    @overload
    def substitute(
        self,
        text: str,
        *,
        output: Literal['string'] = ...,
    ) -> str: ...

    def substitute(
        self,
        text: str,
        *,
        output: Literal['regular', 'backend', 'string'] = 'string',
    ) -> str | HousingType | BackendType:
        value = self._substitute_single_placeholder(text)
        if value is None:
            value = self._substitute_all_placeholders(text)

        if isinstance(value, str):
            cast: BackendType | None = None
            if value.endswith('L'):
                cast = cast_to_backend_long(value[:-1])
            elif value.endswith('D'):
                cast = cast_to_backend_double(value[:-1])
            if cast is not None:
                value = cast

        if output == 'string':
            return backend_into_string(value)
        if output == 'backend':
            return value
        return into_housing_type(value)

    def maybe_cast_value(self, value: HousingType | BackendType) -> BackendType:
        value = into_backend_type(value)
        if not isinstance(value, str):
            return value
        return value

    def put(
        self,
        key: 'Checkable',
        value: HousingType | BackendType,
    ) -> None:
        self.checkable_mapping[key.into_hashable()] = self.maybe_cast_value(value)

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
