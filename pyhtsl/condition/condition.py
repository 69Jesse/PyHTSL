from .statements import IfStatement, ConditionalMode
from ..expression import Expression

from abc import ABC, abstractmethod
from enum import Enum

from typing import TYPE_CHECKING, final
if TYPE_CHECKING:
    from ..stat import Stat


__all__ = (
    'Condition',
    'Operator',
    'PlaceholderValue',
    'OperatorCondition',
)


class Condition(ABC):
    inverted: bool = False
    __slots__ = ()

    @abstractmethod
    def create_line(self) -> str:
        raise NotImplementedError

    def __invert__(self) -> 'Condition':
        self.inverted = not self.inverted
        return self

    def __str__(self) -> str:
        return ('!' * self.inverted) + self.create_line()


class Operator(Enum):
    Equal = '=='
    GreaterThan = '>'
    LessThan = '<'
    GreaterThanOrEqual = '>='
    LessThanOrEqual = '<='


class PlaceholderValue:
    name: str
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def __add__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.add(self, other)

    def __radd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.radd(other, self)

    def __sub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.sub(self, other)

    def __rsub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.rsub(other, self)

    def __mul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.mul(self, other)

    def __rmul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.rmul(other, self)

    def __truediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.truediv(self, other)

    def __rtruediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.rtruediv(other, self)

    def __floordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.floordiv(self, other)

    def __rfloordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.rfloordiv(other, self)

    def __neg__(self) -> Expression:
        return Expression.neg(self)

    def __abs__(self) -> Expression:
        return Expression.abs(self)

    def sign(self) -> Expression:
        return Expression.sign(self)

    @staticmethod
    def equals(
        left: 'Stat | PlaceholderValue | Expression',
        right: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.Equal)

    @staticmethod
    def not_equal(
        left: 'Stat | PlaceholderValue | Expression',
        right: 'Stat | PlaceholderValue | Expression | int',
    ) -> IfStatement:
        """Not equal does not exist on housing, so we do a little magic"""
        return IfStatement([
            OperatorCondition(left, right, Operator.LessThan),
            OperatorCondition(left, right, Operator.GreaterThan),
        ], mode=ConditionalMode.OR)

    @staticmethod
    def greater_than(
        left: 'Stat | PlaceholderValue | Expression',
        right: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.GreaterThan)

    @staticmethod
    def less_than(
        left: 'Stat | PlaceholderValue | Expression',
        right: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.LessThan)

    @staticmethod
    def greater_than_or_equal(
        left: 'Stat | PlaceholderValue | Expression',
        right: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.GreaterThanOrEqual)

    @staticmethod
    def less_than_or_equal(
        left: 'Stat | PlaceholderValue | Expression',
        right: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.LessThanOrEqual)

    def __eq__(
        self,
        other: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return PlaceholderValue.equals(self, other)

    def __ne__(
        self,
        other: 'Stat | PlaceholderValue | Expression | int',
    ) -> IfStatement:
        return PlaceholderValue.not_equal(self, other)

    def __gt__(
        self,
        other: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return PlaceholderValue.greater_than(self, other)

    def __lt__(
        self,
        other: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return PlaceholderValue.less_than(self, other)

    def __ge__(
        self,
        other: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return PlaceholderValue.greater_than_or_equal(self, other)

    def __le__(
        self,
        other: 'Stat | PlaceholderValue | Expression | int',
    ) -> Condition:
        return PlaceholderValue.less_than_or_equal(self, other)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'placeholder "{self.name}"'


Expression._placeholder_value_cls = PlaceholderValue


@final
class OperatorCondition(Condition):
    left: 'Stat | PlaceholderValue | Expression'
    right: 'Stat | PlaceholderValue | Expression | int'
    operator: Operator
    def __init__(
        self,
        left: 'Stat | PlaceholderValue | Expression',
        right: 'Stat | PlaceholderValue | Expression | int',
        operator: Operator,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator

    def create_line(self) -> str:
        return f'{repr(self.left)} {self.operator.value} "{str(self.right)}"'
