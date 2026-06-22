from typing import Self, final

from ..expression.expression import Expression

__all__ = (
    'ParkourCheckpointExpression',
    'parkour_checkpoint',
)


@final
class ParkourCheckpointExpression(Expression):
    def into_htsl(self) -> str:
        return 'parkCheck'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, ParkourCheckpointExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def parkour_checkpoint() -> None:
    ParkourCheckpointExpression().write()
