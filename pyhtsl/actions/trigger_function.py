from typing import TYPE_CHECKING, Self, final

from ..expression.expression import Expression
from ..utils.log import log
from .function import Function

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


__all__ = (
    'TriggerFunctionExpression',
    'trigger_function',
)


@final
class TriggerFunctionExpression(Expression):
    function: Function
    trigger_for_all_players: bool

    def __init__(
        self,
        function: Function,
        trigger_for_all_players: bool = False,
    ) -> None:
        self.function = function
        self.trigger_for_all_players = trigger_for_all_players

    def into_htsl(self) -> str:
        return f'function {self.inline_quoted(self.function.name)} {self.inline(self.trigger_for_all_players)}'

    def cloned(self) -> Self:
        return self.__class__(
            function=self.function,
            trigger_for_all_players=self.trigger_for_all_players,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, TriggerFunctionExpression):
            return False
        return (
            self.function.name == other.function.name
            and self.trigger_for_all_players == other.trigger_for_all_players
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.function.name} all_players={self.trigger_for_all_players}>'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        if self.trigger_for_all_players:
            log(
                f'Function \x1b[38;2;255;0;0m"{self.function.name}"\x1b[0m has \x1b[38;2;0;255;0mtrigger_for_all_players\x1b[0m set to True, but this has \x1b[38;2;0;255;0mno effect\x1b[0m during execution'
            )
        if self.function.name in context.functions_on_cooldown_for_ticks:
            ticks = context.functions_on_cooldown_for_ticks[self.function.name]
            log(
                f'Function \x1b[38;2;255;0;0m"{self.function.name}"\x1b[0m is on cooldown for \x1b[38;2;0;255;0m{ticks} more tick{"s" * (ticks != 1)}\x1b[0m, so it will \x1b[38;2;0;255;0mnot be executed\x1b[0m'
            )
            return
        if self.function.block is None:
            log(
                f'Function \x1b[38;2;255;0;0m"{self.function.name}"\x1b[0m has no expression block attached, \x1b[38;2;0;255;0mnothing will be executed\x1b[0m'
            )
            return
        context.functions_on_cooldown_for_ticks[self.function.name] = 4
        self.function.block.execute_all_expressions(context)


def trigger_function(
    function: Function | str,
    trigger_for_all_players: bool = False,
) -> None:
    function = function if isinstance(function, Function) else Function(function)
    TriggerFunctionExpression(
        function=function,
        trigger_for_all_players=trigger_for_all_players,
    ).write()
