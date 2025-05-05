from .stat import Stat
from ..public.team import Team

from typing import final, Optional


__all__ = (
    'TeamStat',
)


@final
class TeamStat(Stat):
    team: Optional[Team]
    def __init__(self, name: str, team: Optional[Team | str] = None, /) -> None:
        super().__init__(name)
        self.team = team if isinstance(team, Team) else Team(team) if team is not None else None

    @staticmethod
    def _left_side_keyword() -> str:
        return 'teamvar'

    @staticmethod
    def _right_side_keyword() -> str:
        return 'team'


Team._import_team_stat(TeamStat)
