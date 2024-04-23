from ..writer import LineType
from ..stat.stat import Stat
from .team import Team

from typing import final


__all__ = (
    'TeamStat',
)


@final
class TeamStat(Stat):
    team: 'Team'
    def __init__(self, name: str, team: 'Team | str') -> None:
        super().__init__(name)
        self.team = team if isinstance(team, Team) else Team(team)

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
        return f'{super().get_htsl_formatted()} {self.team.name}'
