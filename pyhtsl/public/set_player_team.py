from ..write import write
from .team import Team


__all__ = (
    'set_player_team',
)


def set_player_team(
    team: Team | str,
) -> None:
    team = team if isinstance(team, Team) else Team(team)
    write(f'setTeam "{team.name}"')
