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
        key = '%player.team.players%'
    else:
        team = team if isinstance(team, Team) else Team(team)
        key = f'%player.team.players/{team.name}%'
    return PlaceholderCheckable(
        assignment_right_side=key,
        comparison_left_side=f'placeholder "{key}"',
        comparison_right_side=key,
        in_string=key,
    )


Team._import_team_players(TeamPlayers)
