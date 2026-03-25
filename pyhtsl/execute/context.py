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
from ..utils.warn import warn
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
    pause_multiplier: float

    started_execution: bool
    checkable_mapping: dict[tuple[object, ...], BackendType]

    def __init__(
        self,
        *,
        verbose: bool = False,
        expression_callback: Callable[[Expression], None] | None = None,
        pause_multiplier: float = 1,
    ) -> None:
        super().__init__()
        self.verbose = verbose
        self.expression_callback = expression_callback
        self.pause_multiplier = pause_multiplier
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
        for block in self.blocks:
            block.execute(self)

    def _yield(
        self,
        result: BackendType,
        output: Literal['regular', 'backend', 'string'],
    ) -> HousingType | BackendType | str:
        if output == 'string':
            return backend_into_string(result)
        if output == 'backend':
            return result
        return into_housing_type(result)

    @overload
    def get(
        self,
        key: Checkable | str,
        *,
        default: HousingType | BackendType = ...,
        output: Literal['regular'] = ...,
    ) -> HousingType: ...

    @overload
    def get(
        self,
        key: Checkable | str,
        *,
        default: HousingType | BackendType = ...,
        output: Literal['backend'],
    ) -> BackendType: ...

    @overload
    def get(
        self,
        key: Checkable | str,
        *,
        default: HousingType | BackendType = ...,
        output: Literal['string'],
    ) -> str: ...

    def get(
        self,
        key: Checkable | str,
        *,
        default: HousingType | BackendType = '',
        output: Literal['regular', 'backend', 'string'] = 'regular',
    ) -> HousingType | BackendType | str:
        if isinstance(key, str):
            return self.substitute(key, output=output)

        value = self.checkable_mapping.get(
            key.into_hashable(),
            None,
        )
        if value is None:
            value = key.get_backend_fallback_value()
        if value is None:
            value = into_backend_type(default)

        return self._yield(value, output=output)

    def get_backend(
        self,
        key: Checkable | HousingType,
        default: BackendType | HousingType = '',
    ) -> BackendType:
        if not isinstance(key, Checkable):
            value = into_backend_type(key)
            if isinstance(value, str):
                value = self.substitute(value, output='backend')
            return value
        return self.get(key, default=default, output='backend')

    def _walk_subclasses[T](self, cls: type[T]) -> Generator[type[T], None, None]:
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

    def _has_any_placeholders(self, text: str) -> bool:
        for pattern, _ in self._placeholders_and_factories():
            if pattern.search(text) is not None:
                return True
        return False

    def _is_in_quotes(self, text: str) -> bool:
        return text.startswith('"') and text.endswith('"')

    def _remove_quotes(self, text: str) -> str:
        if self._is_in_quotes(text):
            return text[1:-1]
        return text

    def _maybe_cast_to_backend(self, text: str) -> BackendType | None:
        if text.endswith('L'):
            return cast_to_backend_long(text[:-1])
        elif text.endswith('D'):
            return cast_to_backend_double(text[:-1])
        if (new_value := cast_to_backend_long(text)) is not None:
            return new_value
        if (new_value := cast_to_backend_double(text)) is not None:
            return new_value
        return None

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
        if not self._is_in_quotes(text):
            if (new_value := self._substitute_single_placeholder(text)) is not None:
                return self._yield(new_value, output=output)
            if (new_value := self._maybe_cast_to_backend(text)) is not None:
                return self._yield(new_value, output=output)

        value = self._remove_quotes(text)
        if not self._has_any_placeholders(value):
            return self._yield(value, output=output)

        value = self._substitute_all_placeholders(value)

        if cast and (new_value := self._maybe_cast_to_backend(value)) is not None:
            value = new_value

        return self._yield(value, output=output)

    def put(
        self,
        key: Checkable,
        value: HousingType | BackendType,
        *,
        ignore_warning: bool = False,
    ) -> None:
        if not ignore_warning and len(self.blocks) > 0:
            warn(
                'Putting values into the context should be done BEFORE writing any expressions, since this line is ALWAYS ran, even, for example, if it looks like it is behind a condition that may not hold.',
            )

        value = into_backend_type(value)
        if isinstance(value, str):
            value = self.substitute(value)
        self.checkable_mapping[key.into_hashable()] = value

    def pop(self, key: Checkable) -> None:
        self.checkable_mapping.pop(key.into_hashable(), None)

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
