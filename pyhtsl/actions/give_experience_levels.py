from typing import Self, final

from ..expression.expression import Expression

__all__ = ('give_experience_levels',)


@final
class GiveExperienceLevelsExpression(Expression):
    levels: int

    def __init__(self, levels: int) -> None:
        self.levels = levels

    def into_htsl(self) -> str:
        return f'xpLevel {self.levels}'

    def cloned(self) -> Self:
        return self.__class__(levels=self.levels)

    def equals(self, other: object) -> bool:
        if not isinstance(other, GiveExperienceLevelsExpression):
            return False
        return self.levels == other.levels

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.levels}>'


def give_experience_levels(levels: int) -> None:
    GiveExperienceLevelsExpression(levels=levels).write()
