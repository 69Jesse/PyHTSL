from collections.abc import Iterable
from typing import Self, final

from ..expression.expression import Expression
from ..stats.global_stat import GlobalStat
from ..stats.player_stat import PlayerStat
from ..stats.team_stat import TeamStat
from .function import Function

__all__ = ('trigger_function',)


@final
class TriggerFunctionExpression(Expression):
    function: Function
    trigger_for_all_players: bool

    def __init__(
        self, function: Function, trigger_for_all_players: bool = False
    ) -> None:
        self.function = function
        self.trigger_for_all_players = trigger_for_all_players

    def into_htsl(self) -> str:
        return f'function {self.inline_quoted(self.function.name)} {self.inline(self.trigger_for_all_players)}'

    def cloned(self) -> Self:
        return self.__class__(
            function=self.function, trigger_for_all_players=self.trigger_for_all_players
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


def trigger_function(
    function: Function | str,
    trigger_for_all_players: bool = False,
    *,
    parameters: Iterable[PlayerStat | GlobalStat | TeamStat | int] | None = None,
) -> None:
    function = function if isinstance(function, Function) else Function(function)
    if parameters is not None:
        parameters = tuple(parameters)
        if len(parameters) != len(function.parameters):
            raise TypeError(
                f'Expected {len(function.parameters)} parameters, got {len(parameters)}.'
            )
        for i, (param, expected_param) in enumerate(
            zip(parameters, function.parameters, strict=False)
        ):
            if type(param) not in (PlayerStat, GlobalStat, TeamStat, int):
                raise TypeError(
                    f'Parameter {i} must be either "{PlayerStat.__name__}", "{GlobalStat.__name__}", "{TeamStat.__name__}", or "{int.__name__}", not "{type(param).__name__}".'
                )
            stat: PlayerStat | GlobalStat | TeamStat = expected_param.cls(
                name=expected_param.name
            )  # type: ignore
            stat.value = param
    TriggerFunctionExpression(
        function=function, trigger_for_all_players=trigger_for_all_players
    ).write()
