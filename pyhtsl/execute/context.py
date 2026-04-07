import re
import time
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
from .expressions.run_execution_expression import CallbackType, RunExecutionExpression
from .schedulers import ActionScheduler, DelayedActionScheduler
from .signal import ExitSignal, PauseSignal

__all__ = ('ExecutionContext',)


class ExecutionContext(Container):
    verbose: bool
    expression_callback: Callable[[Expression], None] | None
    ignore_action_limits: bool
    pause_multiplier: float
    volume_multiplier: float

    started_execution: bool
    checkable_mapping: dict[tuple[object, ...], BackendType]
    functions_on_cooldown_for_ticks: dict[str, int]
    schedulers: list[ActionScheduler]

    def __init__(
        self,
        *,
        verbose: bool = False,
        expression_callback: Callable[[Expression], None] | None = None,
        ignore_action_limits: bool = False,
        pause_multiplier: float = 1,
        volume_multiplier: float = 1.0,
    ) -> None:
        super().__init__()
        self.verbose = verbose
        self.expression_callback = expression_callback
        self.ignore_action_limits = ignore_action_limits
        self.pause_multiplier = pause_multiplier
        self.volume_multiplier = volume_multiplier
        self.started_execution = False
        self.checkable_mapping = {}
        self.functions_on_cooldown_for_ticks = {}
        self.schedulers = []

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
        self.run_tick_loop()

    def schedule_continuation(self, continuation: list[Expression], ticks: int) -> None:
        self.schedulers.append(DelayedActionScheduler(continuation, ticks))

    def run_expressions(self, expressions: list[Expression]) -> None:
        for i, expr in enumerate(expressions):
            try:
                expr.execute(self)
            except PauseSignal as sig:
                sig.continuation.extend(expressions[i + 1 :])
                raise

    def run_tick_loop(self) -> None:
        while self.schedulers:
            time.sleep((1 / 20) * self.pause_multiplier)
            self.tick()

    def tick(self) -> None:
        for name in list(self.functions_on_cooldown_for_ticks):
            self.functions_on_cooldown_for_ticks[name] -= 1
            if self.functions_on_cooldown_for_ticks[name] <= 0:
                del self.functions_on_cooldown_for_ticks[name]

        current_schedulers = self.schedulers
        self.schedulers = []

        next_schedulers: list[ActionScheduler] = []
        for scheduler in current_schedulers:
            expressions = scheduler.tick()
            if expressions is not None:
                try:
                    self.run_expressions(expressions)
                except PauseSignal as sig:
                    next_schedulers.append(
                        DelayedActionScheduler(sig.continuation, sig.ticks)
                    )
                except ExitSignal:
                    pass
            if scheduler.has_next():
                next_schedulers.append(scheduler)
        self.schedulers = next_schedulers + self.schedulers

    def should_fix_action_limits(self) -> bool:
        return not self.ignore_action_limits

    @overload
    def _get_raw(self, key: Checkable) -> BackendType | None: ...

    @overload
    def _get_raw(self, key: Checkable, *, default: BackendType) -> BackendType: ...

    def _get_raw(
        self,
        key: Checkable,
        *,
        default: BackendType | None = None,
    ) -> BackendType | None:
        return self.checkable_mapping.get(key.into_hashable(), default)

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

    def _substitute_single_placeholder(
        self,
        placeholder: str,
        *,
        default: BackendType,
    ) -> BackendType | None:
        for pattern, factory in self._placeholders_and_factories():
            match = pattern.fullmatch(placeholder)
            if match is not None:
                return self._get_raw(factory(match), default=default)
        return None

    def _substitute_all_placeholders(self, text: str) -> str:
        for pattern, factory in self._placeholders_and_factories():

            def replace_placeholder(match: re.Match[str]) -> str:
                value = self._get_raw(factory(match), default='')  # noqa: B023
                return backend_into_string(value)

            text = pattern.sub(replace_placeholder, text)

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

    def _substitute(self, key: str, *, default: BackendType) -> BackendType:
        if (
            value := self._substitute_single_placeholder(key, default=default)
        ) is not None:
            return value
        return self._substitute_all_placeholders(key)

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        default: HousingType | BackendType = ...,
        cast: bool = True,
        output: Literal['regular'] = ...,
    ) -> HousingType: ...

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        default: HousingType | BackendType = ...,
        cast: bool = True,
        output: Literal['backend'],
    ) -> BackendType: ...

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        default: HousingType | BackendType = ...,
        cast: bool = True,
        output: Literal['string'],
    ) -> str: ...

    def get(
        self,
        key: Checkable | HousingType,
        *,
        default: HousingType | BackendType = '',
        cast: bool = True,
        output: Literal['regular', 'backend', 'string'] = 'regular',
    ) -> HousingType | BackendType | str:
        if isinstance(key, Checkable):
            key = key.into_string_rhs()

        if isinstance(key, str):
            value = self._substitute(key, default=into_backend_type(default))
        else:
            value = into_backend_type(key)

        if isinstance(value, str):
            assert isinstance(key, str)
            value = self._remove_quotes(value)
            if (
                cast
                and self._has_any_placeholders(key)
                and (new_value := self._maybe_cast_to_backend(value)) is not None
            ):
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
            value = self.get(value, output='backend')
        self.checkable_mapping[key.into_hashable()] = value

    def pop(self, key: Checkable) -> None:
        self.checkable_mapping.pop(key.into_hashable(), None)

    def write_or_execute(self, expression: Expression) -> None:
        if self.started_execution:
            expression.execute(self)
        else:
            self.write_expression(expression)

    def print(
        self,
        *values: object | Callable[[], object] | Callable[['ExecutionContext'], object],
        cast: bool = False,
    ) -> None:
        self.write_or_execute(
            PrintExecutionExpression(
                values=values,
                cast=cast,
            )
        )

    def assert_all(
        self,
        *conditions: Condition
        | Callable[[], Condition]
        | Callable[['ExecutionContext'], Condition],
        message: object = None,
    ) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                conditions,
                mode=ConditionalMode.AND,
                message=str(message) if message is not None else None,
            )
        )

    def assert_any(
        self,
        *conditions: Condition
        | Callable[[], Condition]
        | Callable[['ExecutionContext'], Condition],
        message: object = None,
    ) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                conditions,
                mode=ConditionalMode.OR,
                message=str(message) if message is not None else None,
            )
        )

    def run(self, callback: CallbackType) -> None:
        self.write_or_execute(
            RunExecutionExpression(callback=callback),
        )
