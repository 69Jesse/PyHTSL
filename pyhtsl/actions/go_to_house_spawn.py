from typing import Self, final

from ..expression.expression import Expression

__all__ = ('go_to_house_spawn',)


@final
class GoToHouseSpawnExpression(Expression):
    def into_htsl(self) -> str:
        return 'houseSpawn'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, GoToHouseSpawnExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def go_to_house_spawn() -> None:
    GoToHouseSpawnExpression().write()
