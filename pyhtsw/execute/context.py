import re
import time
from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from types import TracebackType
from typing import TYPE_CHECKING, Literal, overload

from ..checkable import Checkable
from ..container import Container, override_write_expression
from ..expression.condition.condition import Condition
from ..expression.condition.conditional_expression import ConditionalMode
from ..expression.expression import Expression
from ..expression.housing_type import HousingType
from ..utils.log import log
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
from .player import ExecutionPlayer
from .schedulers import ActionScheduler, DelayedActionScheduler
from .signal import ExitSignal, PauseSignal

if TYPE_CHECKING:
    from ..actions.function import Function

__all__ = ('ExecutionContext',)


type PlayersArg = int | Iterable[str | ExecutionPlayer] | None


class ExecutionContext(Container):
    verbose: bool
    expression_callback: Callable[[Expression], None] | None
    pause_multiplier: float
    volume_multiplier: float

    started_execution: bool
    global_mapping: dict[tuple[object, ...], BackendType]
    players: list[ExecutionPlayer]
    current_player: ExecutionPlayer
    schedulers: list[ActionScheduler]

    def __init__(
        self,
        *,
        players: PlayersArg = None,
        ignore_action_limits: bool = False,
        allow_nested_expressions: bool = False,
        verbose: bool = False,
        expression_callback: Callable[[Expression], None] | None = None,
        pause_multiplier: float = 1.0,
        volume_multiplier: float = 0.1,
    ) -> None:
        super().__init__(
            ignore_action_limits=ignore_action_limits,
            allow_nested_expressions=allow_nested_expressions,
        )
        self.verbose = verbose
        self.expression_callback = expression_callback
        self.pause_multiplier = pause_multiplier
        self.volume_multiplier = volume_multiplier
        self.started_execution = False
        self.global_mapping = {}
        self.players = []
        self._setup_players(players)
        self.current_player = self.players[0]
        self.schedulers = []

    def _setup_players(self, players: PlayersArg) -> None:
        if players is None:
            self.add_player()
            return
        if isinstance(players, int):
            for index in range(max(players, 1)):
                self.add_player(f'player{index + 1}')
            return
        added = False
        for player in players:
            self.add_player(player)
            added = True
        if not added:
            self.add_player()

    def add_player(
        self,
        player: 'str | ExecutionPlayer | None' = None,
    ) -> ExecutionPlayer:
        resolved = (
            player if isinstance(player, ExecutionPlayer) else ExecutionPlayer(player)
        )
        resolved.context = self
        self.players.append(resolved)
        if resolved.name is not None:
            from ..actions.player_name import PlayerName

            self.put(PlayerName, resolved.name, ignore_warning=True, player=resolved)
        return resolved

    @contextmanager
    def using_player(self, player: ExecutionPlayer) -> Generator[None]:
        previous = self.current_player
        self.current_player = player
        try:
            yield
        finally:
            self.current_player = previous

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
        # This context is already popped off the stack; swallow any stray
        # `write()` during the run so it does not leak into the global container.
        with override_write_expression(lambda _: None):
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
        for player in self.players:
            cooldowns = player.functions_on_cooldown_for_ticks
            for name in list(cooldowns):
                cooldowns[name] -= 1
                if cooldowns[name] <= 0:
                    del cooldowns[name]

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
                        DelayedActionScheduler(sig.continuation, sig.ticks),
                    )
                except ExitSignal:
                    pass
            if scheduler.has_next():
                next_schedulers.append(scheduler)
        self.schedulers = next_schedulers + self.schedulers

    def _mapping_for(
        self,
        key: Checkable,
        player: ExecutionPlayer | None,
    ) -> dict[tuple[object, ...], BackendType]:
        if key.is_execution_player_scoped():
            return (player if player is not None else self.current_player).mapping
        return self.global_mapping

    @overload
    def _get_raw(
        self,
        key: Checkable,
        *,
        player: ExecutionPlayer | None = ...,
    ) -> BackendType | None: ...

    @overload
    def _get_raw(
        self,
        key: Checkable,
        *,
        default: BackendType,
        player: ExecutionPlayer | None = ...,
    ) -> BackendType: ...

    def _get_raw(
        self,
        key: Checkable,
        *,
        default: BackendType | None = None,
        player: ExecutionPlayer | None = None,
    ) -> BackendType | None:
        value = self._mapping_for(key, player).get(key.into_hashable())
        if value is not None:
            return value
        fallback = key.get_backend_fallback_value()
        if fallback is not None:
            return fallback
        return default

    def get_raw(
        self,
        key: Checkable,
        *,
        default: HousingType | None = None,
        player: ExecutionPlayer | None = None,
    ) -> HousingType:
        if default is None:
            default = key.internal_type.default_housing_type()
            if default is None:
                default = ''
        return into_housing_type(
            self._get_raw(key, default=into_backend_type(default), player=player),
        )

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

    def _substitute_all_placeholders(
        self,
        text: str,
        *,
        player: ExecutionPlayer | None = None,
    ) -> str:
        for pattern, factory in Checkable.iter_pattern_factories():

            def replace_placeholder(match: re.Match[str]) -> str:
                value = self._get_raw(factory(match), default='', player=player)  # noqa: B023
                return backend_into_string(value)

            text = pattern.sub(replace_placeholder, text)

        return text

    def _has_any_placeholders(self, text: str) -> bool:
        for pattern, _ in Checkable.iter_pattern_factories():
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
        last = text[-1:].upper()
        base = text[:-1]
        if (
            base
            and last in ('L', 'D')
            and (
                cast_to_backend_long(base) is not None
                or cast_to_backend_double(base) is not None
            )
        ):
            if last == 'L':
                return cast_to_backend_long(base.split('.')[0])
            return cast_to_backend_double(base)
        if (new_value := cast_to_backend_long(text)) is not None:
            return new_value
        if (new_value := cast_to_backend_double(text)) is not None:
            return new_value
        return None

    def _substitute(
        self,
        key: str,
        *,
        default: BackendType,
        player: ExecutionPlayer | None = None,
    ) -> BackendType:
        seen: set[str] = set()
        while key not in seen:
            seen.add(key)
            matched = False
            for pattern, factory in Checkable.iter_pattern_factories():
                match = pattern.fullmatch(key)
                if match is None:
                    continue
                value = self._get_raw(factory(match), default=default, player=player)
                if not isinstance(value, str):
                    return value
                key = value
                matched = True
                break
            if not matched:
                return self._substitute_all_placeholders(key, player=player)
        return key

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['regular'] = ...,
        player: ExecutionPlayer | None = ...,
    ) -> HousingType: ...

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['backend'],
        player: ExecutionPlayer | None = ...,
    ) -> BackendType: ...

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['string'],
        player: ExecutionPlayer | None = ...,
    ) -> str: ...

    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['regular', 'backend', 'string'] = 'regular',
        player: ExecutionPlayer | None = None,
    ) -> HousingType | BackendType | str:
        if isinstance(key, Checkable):
            key = key.into_string_rhs()

        if isinstance(key, str):
            value = self._substitute(key, default='', player=player)
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
        player: ExecutionPlayer | None = None,
    ) -> None:
        if not ignore_warning and any(not block.is_empty() for block in self.blocks):
            warn(
                'Putting values into the context should be done BEFORE writing any expressions, since this line is ALWAYS ran, even, for example, if it looks like it is behind a condition that may not hold.',
            )
        self._mapping_for(key, player)[key.into_hashable()] = into_backend_type(value)

    def pop(self, key: Checkable, *, player: ExecutionPlayer | None = None) -> None:
        self._mapping_for(key, player).pop(key.into_hashable(), None)

    def execute_function(
        self,
        function: 'Function',
        *,
        all_players: bool,
    ) -> None:
        """Run `function` for the current player, or — when `all_players` —
        once for every player. The per-player 4-tick cooldown is what excludes
        a caster that just ran the function from its own `… true` fan-out, so a
        single self-triggering function runs "for everyone but me"."""
        players = list(self.players) if all_players else [self.current_player]
        for player in players:
            with self.using_player(player):
                self._invoke_function(function, player)

    def _invoke_function(self, function: 'Function', player: ExecutionPlayer) -> None:
        cooldowns = player.functions_on_cooldown_for_ticks
        if function.name in cooldowns:
            if self.verbose:
                log(
                    f'Function \x1b[38;2;255;0;0m"{function.name}"\x1b[0m is on cooldown '
                    f'for \x1b[38;2;0;255;0m{player.name}\x1b[0m, skipping',
                )
            return
        cooldowns[function.name] = 4
        if function.block is None or function.block.is_empty():
            log(
                f'Function \x1b[38;2;255;0;0m"{function.name}"\x1b[0m has no expressions '
                'to execute. If this is unexpected, consider using the '
                '\x1b[38;2;255;0;0mexecute\x1b[0m decorator so it is finalized first.',
            )
            return
        function.block.execute_all_expressions(self)

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
            ),
        )

    def assert_all(
        self,
        *conditions: Condition
        | Callable[[], Condition | None]
        | Callable[['ExecutionContext'], Condition | None],
        message: object = None,
    ) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                conditions,
                mode=ConditionalMode.ALL,
                message=str(message) if message is not None else None,
            ),
        )

    def assert_any(
        self,
        *conditions: Condition
        | Callable[[], Condition | None]
        | Callable[['ExecutionContext'], Condition | None],
        message: object = None,
    ) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                conditions,
                mode=ConditionalMode.ANY,
                message=str(message) if message is not None else None,
            ),
        )

    def run(self, callback: CallbackType) -> None:
        self.write_or_execute(
            RunExecutionExpression(callback=callback),
        )
