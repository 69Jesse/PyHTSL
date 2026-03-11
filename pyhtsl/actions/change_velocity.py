from typing import Self, final

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import NumericHousingType

__all__ = ('change_velocity',)


@final
class ChangeVelocityExpression(Expression):
    x: Checkable | NumericHousingType
    y: Checkable | NumericHousingType
    z: Checkable | NumericHousingType

    def __init__(
        self,
        x: Checkable | NumericHousingType,
        y: Checkable | NumericHousingType,
        z: Checkable | NumericHousingType,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z

    def into_htsl(self) -> str:
        return f'changeVelocity {self.inline(self.x)} {self.inline(self.y)} {self.inline(self.z)}'

    def cloned(self) -> Self:
        return self.__class__(
            x=self.cloned_or_same(self.x),
            y=self.cloned_or_same(self.y),
            z=self.cloned_or_same(self.z),
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, ChangeVelocityExpression):
            return False
        return (
            self.equals_or_eq(self.x, other.x)
            and self.equals_or_eq(self.y, other.y)
            and self.equals_or_eq(self.z, other.z)
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<x={self.x} y={self.y} z={self.z}>'


def change_velocity(
    x: Checkable | NumericHousingType,
    y: Checkable | NumericHousingType,
    z: Checkable | NumericHousingType,
) -> None:
    ChangeVelocityExpression(x=x, y=y, z=z).write()
