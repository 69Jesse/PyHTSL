from typing import Self, final

from ..expression.expression import Expression

__all__ = (
    'FullHealExpression',
    'full_heal',
)


@final
class FullHealExpression(Expression):
    def into_htsl(self) -> str:
        return 'fullHeal'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, FullHealExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def full_heal() -> None:
    FullHealExpression().write()
