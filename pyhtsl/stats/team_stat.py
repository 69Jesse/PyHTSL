import re
from typing import final

from ..actions.team import Team
from ..expression.housing_type import HousingType, housing_type_from_string
from ..internal_type import InternalType
from .player_stat import _split_parts
from .stat import Stat

__all__ = ('TeamStat',)


def _team_stat_factory(match: re.Match[str]) -> 'TeamStat':
    parts = _split_parts(match.group(1))
    name = parts[0] if len(parts) > 0 else ''
    team = Team(parts[1]) if len(parts) > 1 else None
    stat = TeamStat(name, team)
    if len(parts) > 2:
        stat = stat.with_fallback(housing_type_from_string(parts[2]))
    return stat


@final
class TeamStat(
    Stat,
    pattern=re.compile(r'%var\.team/([^%]+)%'),
    pattern_factory=_team_stat_factory,
):
    team: Team | None

    def __init__(
        self,
        name: str,
        /,
        team: Team | str | None = None,
        *,
        internal_type: InternalType = InternalType.ANY,
        fallback_value: HousingType | None = None,
        auto_unset: bool = True,
    ) -> None:
        super().__init__(
            name,
            internal_type=internal_type,
            fallback_value=fallback_value,
            auto_unset=auto_unset,
        )
        self.team = (
            team if isinstance(team, Team) else Team(team) if team is not None else None
        )

    def into_hashable(self) -> tuple[object, ...]:
        return (
            *super().into_hashable(),
            self.team.name if self.team is not None else None,
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
