from ..writer import LineType
from ..stat.stat import Stat
from .team import Team

from typing import final, Optional


__all__ = (
    'TeamStat',
)


@final
class TeamStat(Stat):
    team: Optional['Team']
    def __init__(self, name: str, team: Optional['Team | str'] = None) -> None:
        super().__init__(name)
        self.team = team if isinstance(team, Team) else Team(team) if team is not None else None

    @staticmethod
    def get_prefix() -> str:
        return 'teamstat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'team'

    @property
    def line_type(self) -> LineType:
        return LineType.team_stat_change

    def get_htsl_formatted(self) -> str:
        return f'{super().get_htsl_formatted()} {self.team.name if self.team is not None else 'None'}'


Team.stat = lambda self, key: TeamStat(key, self)
