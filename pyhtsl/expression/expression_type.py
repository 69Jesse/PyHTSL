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

    def __repr__(self) -> str:
        return self.value
