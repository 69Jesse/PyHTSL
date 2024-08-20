from ..condition import PlaceholderValue
from .team import Team

from typing import Optional


__all__ = (
    'TeamPlayers',
)


def TeamPlayers(
    team: Optional[Team | str],
) -> PlaceholderValue:
    if team is None:
        return PlaceholderValue('%player.team.players%')
    team = team if isinstance(team, Team) else Team(team)
    return PlaceholderValue(f'%player.team.players/{team.name}%')


Team.players = lambda self: TeamPlayers(self)
