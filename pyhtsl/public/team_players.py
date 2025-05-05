from ..placeholders import PlaceholderCheckable
from .team import Team

from typing import Optional


__all__ = (
    'TeamPlayers',
)


def TeamPlayers(
    team: Optional[Team | str],
) -> PlaceholderCheckable:
    if team is None:
        return PlaceholderCheckable('%player.team.players%')
    team = team if isinstance(team, Team) else Team(team)
    return PlaceholderCheckable(f'%player.team.players/{team.name}%')


Team._import_team_players(TeamPlayers)
