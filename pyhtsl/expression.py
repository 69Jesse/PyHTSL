from enum import Enum
import os

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from .stat import Stat


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

    def __add__(self, other: 'Expression | Stat | int') -> 'Expression':
        expr = Expression(self, other, ExpressionType.Increment)
        HANDLER.add_expression(expr)
        return expr

    def __sub__(self, other: 'Expression | Stat | int') -> 'Expression':
        expr = Expression(self, other, ExpressionType.Decrement)
        HANDLER.add_expression(expr)
        return expr

    def __mul__(self, other: 'Expression | Stat | int') -> 'Expression':
        expr = Expression(self, other, ExpressionType.Multiply)
        HANDLER.add_expression(expr)
        return expr

    def __truediv__(self, other: 'Expression | Stat | int') -> 'Expression':
        expr = Expression(self, other, ExpressionType.Divide)
        HANDLER.add_expression(expr)
        return expr

    def __floordiv__(self, other: 'Expression | Stat | int') -> 'Expression':
        return self.__truediv__(other)

    def __neg__(self) -> 'Expression':
        return self.__mul__(-1)
