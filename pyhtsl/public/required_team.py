from ..condition import TinyCondition
from .team import Team

from typing import Optional, final


__all__ = (
    'RequiredTeam',
)


@final
class RequiredTeam(TinyCondition):
    team: Optional[Team]
    def __init__(
        self,
        team: Optional[Team | str],
    ) -> None:
        self.team = team if not isinstance(team, str) else Team(team)

    def __str__(self) -> str:
        return f'hasTeam "{self.team.name if self.team is not None else "None"}"'
