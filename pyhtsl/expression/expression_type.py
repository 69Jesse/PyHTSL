from enum import Enum


__all__ = (
    'ExpressionType',
)


class ExpressionType(Enum):
    Increment = '+='
    Decrement = '-='
    Set = '='
    Multiply = '*='
    Divide = '/='
