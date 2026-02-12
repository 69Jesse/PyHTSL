from typing import final

from ..actions.team import Team
from .stat import Stat

__all__ = ('TeamStat',)


@final
class TeamStat(Stat):
    team: Team | None

    def __init__(self, name: str, team: Team | str | None = None, /) -> None:
        super().__init__(name)
        self.team = (
            team if isinstance(team, Team) else Team(team) if team is not None else None
        )

    @staticmethod
    def _left_side_keyword() -> str:
        return 'teamvar'

    @staticmethod
    def _right_side_keyword() -> str:
        return 'team'

    def into_assignment_left_side(self) -> str:
        value = super().into_assignment_left_side()
        if self.team is not None:
            return f'{value} "{self.team.name}"'
        return value

    def _as_string_second(self, include_fallback_value: bool = True) -> str:
        value = super()._as_string_second(include_fallback_value=include_fallback_value)
        if self.team is not None or value:
            name = self.team.name if isinstance(self.team, Team) else 'None'
            if ' ' in name:
                name = f'"{name}"'  # this will break htsl :( waiting on htsw :D
            return f' {name}{value}'
        return value

    def equals_raw(self, other: object) -> bool:
        if not super().equals_raw(other):
            return False
        if not isinstance(other, TeamStat):
            return False
        return self.team == other.team

    def cloned_raw(self) -> 'TeamStat':
        return TeamStat(self.name, self.team)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}, {repr(self.team)} {self.internal_type.name}>'
