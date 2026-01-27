from ..condition.base_condition import BaseCondition
from .team import Team

from typing import final


__all__ = ('RequiredTeam',)


@final
class RequiredTeam(BaseCondition):
    team: Team | None

    def __init__(
        self,
        team: Team | str | None,
    ) -> None:
        self.team = team if not isinstance(team, str) else Team(team)

    def create_line(self) -> str:
        return f'hasTeam "{self.team.name if self.team is not None else "None"}"'
