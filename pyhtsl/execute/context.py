import os
import re
from collections.abc import Callable, Generator
from types import TracebackType
from typing import Literal, overload

from ..checkable import Checkable
from ..container import Container
from ..expression.condition.condition import Condition
from ..expression.condition.conditional_expression import ConditionalMode
from ..expression.expression import Expression
from ..expression.housing_type import HousingType
from ..placeholders import PlaceholderCheckable, PlaceholderEditable
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
        output: Literal['regular'] = ...,
    ) -> HousingType: ...

    @overload
    def get(
        self,
        key: Checkable,
        *,
        default: HousingType | BackendType = ...,
        output: Literal['backend'],
    ) -> BackendType: ...

    @overload
    def get(
        self,
        key: Checkable,
        *,
        default: HousingType | BackendType = ...,
        output: Literal['string'],
    ) -> str: ...

    def get(
        self,
        key: Checkable,
        *,
        default: HousingType | BackendType = '',
        output: Literal['regular', 'backend', 'string'] = 'regular',
    ) -> HousingType | BackendType | str:
        value = self.checkable_mapping.get(
            key.into_hashable(),
            None,
        )
        if value is None:
            if isinstance(key, PlaceholderCheckable | PlaceholderEditable):
                value = key.get_backend_value()
        if value is None:
            value = into_backend_type(default)

        if output == 'string':
            return backend_into_string(value)
        if output == 'backend':
            return value
        return into_housing_type(value)

    def _walk_subclasses(self, cls: type) -> Generator[type, None, None]:
        yield cls
        for subclass in cls.__subclasses__():
            yield from self._walk_subclasses(subclass)

    def _placeholders_and_factories(
        self,
    ) -> list[tuple[re.Pattern[str], Callable[[re.Match[str]], Checkable]]]:
        result: list[tuple[re.Pattern[str], Callable[[re.Match[str]], Checkable]]] = []
        for cls in self._walk_subclasses(Checkable):
            if cls.pattern is not None and cls.pattern_factory is not None:
                result.append((cls.pattern, cls.pattern_factory))
        return result

    def _substitute_single_placeholder(self, placeholder: str) -> BackendType | None:
        for pattern, factory in self._placeholders_and_factories():
            match = pattern.fullmatch(placeholder)
            if match is not None:
                return self.get(factory(match), output='backend')
        return None

    def _substitute_all_placeholders(self, text: str) -> str:
        for pattern, factory in self._placeholders_and_factories():
            text = pattern.sub(
                lambda match: self.get(factory(match), output='string'),  # noqa: B023
                text,
            )
        return text

    @overload
    def substitute(
        self,
        text: str,
        *,
        cast: bool = True,
        output: Literal['regular'],
    ) -> HousingType: ...

    @overload
    def substitute(
        self,
        text: str,
        *,
        cast: bool = True,
        output: Literal['backend'],
    ) -> BackendType: ...

    @overload
    def substitute(
        self,
        text: str,
        *,
        cast: bool = True,
        output: Literal['string'] = ...,
    ) -> str: ...

    def substitute(
        self,
        text: str,
        *,
        cast: bool = True,
        output: Literal['regular', 'backend', 'string'] = 'string',
    ) -> str | HousingType | BackendType:
        value = self._substitute_single_placeholder(text)
        if value is None:
            value = self._substitute_all_placeholders(text)

        if cast and isinstance(value, str):
            new_value: BackendType | None = None
            if value.endswith('L'):
                new_value = cast_to_backend_long(value[:-1])
            elif value.endswith('D'):
                new_value = cast_to_backend_double(value[:-1])
            if new_value is None:
                new_value = cast_to_backend_long(value) or cast_to_backend_double(value)

            if new_value is not None:
                value = new_value

        if output == 'string':
            return backend_into_string(value)
        if output == 'backend':
            return value
        return into_housing_type(value)

    def put(
        self,
        key: Checkable,
        value: HousingType | BackendType,
    ) -> None:
        value = into_backend_type(value)
        if isinstance(value, str):
            value = self.substitute(value)
        self.checkable_mapping[key.into_hashable()] = value

    def write_or_execute(self, expression: Expression) -> None:
        if self.started_execution:
            expression.execute(self)
        else:
            self.write_expression(expression)

    def print(self, *lines: object, cast: bool = False) -> None:
        self.write_or_execute(
            PrintExecutionExpression(
                line=' '.join(map(str, lines)),
                cast=cast,
            )
        )

    def assert_all(self, *conditions: Condition, message: object = None) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                list(conditions),
                mode=ConditionalMode.AND,
                message=str(message) if message is not None else None,
            )
        )

    def assert_any(self, *conditions: Condition, message: object = None) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                list(conditions),
                mode=ConditionalMode.OR,
                message=str(message) if message is not None else None,
            )
        )
