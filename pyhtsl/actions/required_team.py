from typing import Self, final

from ..expression.condition.condition import Condition
from .team import Team

__all__ = ('RequiredTeam',)


@final
class RequiredTeam(Condition):
    team: Team | None

    def __init__(
        self,
        team: Team | str | None,
    ) -> None:
        self.team = team if not isinstance(team, str) else Team(team)

    def into_htsl_raw(self) -> str:
        name = self.team.name if self.team is not None else 'None'
        return f'hasTeam {self.inline_quoted(name)}'

    def cloned_raw(self) -> Self:
        return self.__class__(
            team=self.team.cloned() if self.team is not None else None,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, RequiredTeam):
            return False
        return self.equals_or_eq(self.team, other.team)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<team={self.team!r} inverted={self.inverted}>'
