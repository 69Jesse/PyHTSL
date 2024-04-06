from enum import Enum
import os

from .stat import Stat

from typing import Optional


__all__ = (
    'HANDLER',
    'ExpressionType',
    'Expression',
)


class ExpressionHandler:
    __slots__ = ()
    
    __expressions: list['Expression'] = []

    def add_expression(self, expression: 'Expression') -> None:
        self.__expressions.append(expression)


HANDLER = ExpressionHandler()


class ExpressionType(Enum):
    Increment = 0
    Decrement = 1
    Set = 2
    Multiply = 3
    Divide = 4


class Expression:
    left: 'Expression | Stat'
    right: 'Expression | Stat | int'
    type: ExpressionType
    id: str
    def __init__(
        self,
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
        type: ExpressionType,
        id: Optional[str] = None,
    ) -> None:
        self.left = left
        self.right = right
        self.type = type
        self.id = id or os.urandom(8).hex()
