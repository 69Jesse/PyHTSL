from typing import TYPE_CHECKING, Self, final

from .expression import Expression

if TYPE_CHECKING:
    from ..stats.stat import Stat


@final
class UnsetExpression(Expression):
    target: 'Stat'

    def __init__(self, target: 'Stat') -> None:
        self.target = target

    def cloned(self) -> Self:
        return self.__class__(self.target.cloned())

    def equals(self, other: object) -> bool:
        if not isinstance(other, UnsetExpression):
            return False
        return self.target.equals(other.target)

    def into_htsl(self) -> str:
        return f'unset {self.target.into_assignment_left_side()}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.target)}>'
