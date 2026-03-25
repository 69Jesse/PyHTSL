from typing import TYPE_CHECKING, Self, final

from ..expression.expression import Expression
from ..utils.log import log
from .function import Function

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


__all__ = ('trigger_function',)


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
            log(f'Function "{self.function.name}" has `trigger_for_all_players` set to True, but this has no effect during execution')
        if self.function.name in context.functions_on_cooldown_for_ticks:
            log(f'Function "{self.function.name}" is on cooldown for {context.functions_on_cooldown_for_ticks[self.function.name]} more ticks, so it will not be executed')
            return
        if self.function.block is None:
            log(f'Function "{self.function.name}" has no expression block attached, so nothing will be executed')
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
