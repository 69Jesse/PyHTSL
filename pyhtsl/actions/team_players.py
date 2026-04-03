import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable
from .team import Team

__all__ = (
    'TeamPlayersPlaceholder',
    'TeamPlayers',
)


def _team_players_factory(match: re.Match[str]) -> 'TeamPlayersPlaceholder':
    team = match.group(1)
    return TeamPlayersPlaceholder(team if team else None)


@final
class TeamPlayersPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(r'%player\.team\.players(?:/([^%]*))?%'),
    pattern_factory=_team_players_factory,
):
    def __init__(self, team: Team | str | None = None) -> None:
        if team is None:
            key = '%player.team.players%'
        else:
            team = team if isinstance(team, Team) else Team(team)
            key = f'%player.team.players/{team.name}%'
        super().__init__(
            as_string=key,
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


def TeamPlayers(
    team: Team | str | None,
) -> TeamPlayersPlaceholder:
    return TeamPlayersPlaceholder(team)
