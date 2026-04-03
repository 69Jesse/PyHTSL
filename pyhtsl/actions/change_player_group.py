from typing import Self, final

from ..expression.expression import Expression
from .group import Group

__all__ = (
    'ChangePlayerGroupExpression',
    'change_player_group',
)


@final
class ChangePlayerGroupExpression(Expression):
    group: Group
    demotion_protection: bool

    def __init__(self, group: Group, demotion_protection: bool = True) -> None:
        self.group = group
        self.demotion_protection = demotion_protection

    def into_htsl(self) -> str:
        return f'changePlayerGroup {self.inline_quoted(self.group.name)} {self.inline(self.demotion_protection)}'

    def cloned(self) -> Self:
        return self.__class__(
            group=self.group, demotion_protection=self.demotion_protection
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, ChangePlayerGroupExpression):
            return False
        return (
            self.group.name == other.group.name
            and self.demotion_protection == other.demotion_protection
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.group.name} demotion_protection={self.demotion_protection}>'


def change_player_group(group: Group | str, demotion_protection: bool = True) -> None:
    group = group if isinstance(group, Group) else Group(group)
    ChangePlayerGroupExpression(
        group=group, demotion_protection=demotion_protection
    ).write()
