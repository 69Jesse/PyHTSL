import os

from .checkable import Checkable
from .housing_type import HousingType
from enum import Enum

from typing import Optional


__all__ = (
    'ExpressionOperator',
    'Expression',
)


class ExpressionOperator(Enum):
    Increment = '+='
    Decrement = '-='
    Set = '='
    Multiply = '*='
    Divide = '/='

    def __repr__(self) -> str:
        return self.value



class Expression(Checkable):
    left: 'Checkable'
    right: 'Checkable | HousingType'
    operator: ExpressionOperator
    id: str
    def __init__(
        self,
        left: 'Checkable',
        right: 'Checkable | HousingType',
        operator: ExpressionOperator,
        id: Optional[str] = None,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator
        self.id = id or os.urandom(8).hex()

    def all_the_way_left(self, value: 'Checkable | HousingType') -> 'Checkable | HousingType':
        while isinstance(value, Expression):
            value = value.left
        return value
