from typing import Self, final

from ..expression.expression import Expression

__all__ = ('kill_player',)


@final
class KillPlayerExpression(Expression):
    def into_htsl(self) -> str:
        return 'kill'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, KillPlayerExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def kill_player() -> None:
    KillPlayerExpression().write()
