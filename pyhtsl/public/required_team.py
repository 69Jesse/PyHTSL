from ..condition import TinyCondition
from .team import Team

from typing import final


__all__ = (
    'RequiredTeam',
)


@final
class RequiredTeam(TinyCondition):
    team: Team
    def __init__(
        self,
        team: Team | str,
    ) -> None:
        self.team = team if isinstance(team, Team) else Team(team)

    def __str__(self) -> str:
        return f'isTeam "{self.team.name}"'
