import os

from ..checkable import Checkable
from ..editable import Editable
from .housing_type import HousingType
from enum import Enum
from .handler import ExpressionHandler, EXPR_HANDLER
from ..internal_type import InternalType

from typing import Optional, final, overload


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


@final
class Expression(Checkable):
    left: Editable
    right: Checkable | HousingType
    operator: ExpressionOperator
    id: str
    def __init__(
        self,
        left: Editable,
        right: Checkable | HousingType,
        operator: ExpressionOperator,
        id: Optional[str] = None,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator
        self.id = id or os.urandom(8).hex()

    @overload
    def _all_the_way_left(self, value: Editable) -> Editable:
        ...

    @overload
    def _all_the_way_left(self, value: Checkable) -> Checkable:
        ...

    @overload
    def _all_the_way_left(self, value: HousingType) -> HousingType:
        ...

    @overload
    def _all_the_way_left(self, value: Checkable | HousingType) -> Checkable | HousingType:
        ...

    def _all_the_way_left(self, value: Checkable | HousingType) -> Checkable | HousingType:
        while isinstance(value, Expression):
            value = value.left
        return value

    @property
    def internal_type(self) -> InternalType:
        return self._all_the_way_left(self).internal_type

    @internal_type.setter
    def internal_type(self, value: InternalType) -> None:
        self._all_the_way_left(self).internal_type = value

    def _in_assignment_left_side(self) -> str:
        return self._all_the_way_left(self)._in_assignment_left_side()

    def _in_assignment_right_side(self, *, include_internal_type: bool = True) -> str:
        return self._all_the_way_left(self)._in_assignment_right_side(include_internal_type=include_internal_type)

    def _in_comparison_left_side(self) -> str:
        return self._in_assignment_left_side()

    def _in_comparison_right_side(self) -> str:
        return self._in_assignment_right_side()

    def _as_string(self) -> str:
        """Pushing here so we can do something like
        foo = PlayerStat('foo')
        chat(f'Hello World! {foo + 1}')
        """
        EXPR_HANDLER.push()
        return self._all_the_way_left(self)._as_string()

    def _equals(self, other: Checkable | HousingType) -> bool:
        if not isinstance(other, Expression):
            return False
        if not self.left.equals(other.left):
            return False
        if isinstance(self.right, HousingType):
            if not isinstance(other.right, HousingType):
                return False
            return self.right == other.right
        return self.right.equals(other.right)

    def _copied(self) -> 'Expression':
        return Expression(
            self.left.copied(),
            self.right.copied() if isinstance(self.right, Checkable) else self.right,
            self.operator,
            self.id,
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.left)} {self.operator.value} {repr(self.right)}>'


Checkable._import_expression(Expression, ExpressionOperator)
Editable._import_expression(Expression, ExpressionOperator)
ExpressionHandler._import_expression(Expression, ExpressionOperator)
