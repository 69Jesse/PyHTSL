from .stat import Stat
from ..checkable import Checkable
from ..expression.housing_type import HousingType
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

    def _equals(self, other: Checkable | HousingType) -> bool:
        if isinstance(other, TeamStat):
            return self.name == other.name and self.team == other.team
        return False

    def copied(self) -> 'TeamStat':
        return TeamStat(self.name, self.team)


Team._import_team_stat(TeamStat)
