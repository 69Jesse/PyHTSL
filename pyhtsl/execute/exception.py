__all__ = (
    'ExecutionException',
    'MismatchedTypeException',
    'NotANumberException',
)


from typing import TYPE_CHECKING, NoReturn

import numpy as np

from ..checkable import Checkable
from ..editable import Editable
from ..expression.housing_type import HousingType
from ..internal_type import InternalType
from .backend_type import BackendType

if TYPE_CHECKING:
    from ..expression.binary_expression import BinaryOperator


class ExecutionException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f'[ERROR] {message}')


def internal_type_to_description(internal_type: InternalType) -> str:
    if internal_type is InternalType.LONG:
        return 'Whole Number'
    if internal_type is InternalType.DOUBLE:
        return 'Decimal Number'
    if internal_type is InternalType.STRING:
        return 'Text'
    raise ValueError(f'Unknown internal type: {internal_type}')


def descriptive_backend_type(value: BackendType) -> str:
    if isinstance(value, np.integer):
        return f'long<{value}>'
    if isinstance(value, np.floating):
        return f'double<{value}>'
    if isinstance(value, str):
        return f'string<{value!r}>'
    raise


class MismatchedTypeException(ExecutionException):
    def __init__(
        self,
        left: InternalType,
        right: InternalType,
    ) -> None:
        super().__init__(
            f'Mismatched type: Tried to modify {internal_type_to_description(left)} with {internal_type_to_description(right)}'
        )

    @staticmethod
    def throw(
        *,
        left: tuple[Editable, BackendType],
        right: tuple[Checkable | HousingType, BackendType],
        operator: 'BinaryOperator',
    ) -> NoReturn:
        left_string = f'{descriptive_backend_type(left[1])} ({left[0].into_string_lhs()})'
        right_string = descriptive_backend_type(right[1]) + (
            f' ({right[0].into_string_rhs()})'
            if isinstance(right[0], Checkable)
            else ''
        )
        raise MismatchedTypeException(
            left=InternalType.from_value(left[1]),
            right=InternalType.from_value(right[1]),
        ) from TypeError(
            f'Housing does not let you modify two values with different types: {left_string} {operator.value} {right_string}'
        )


class NotANumberException(ExecutionException):
    def __init__(self) -> None:
        super().__init__('The value provided is not a number')

    @staticmethod
    def throw(
        *,
        left: tuple[Editable, BackendType],
        right: tuple[Checkable | HousingType, BackendType],
        operator: 'BinaryOperator',
    ) -> NoReturn:
        left_string = f'{descriptive_backend_type(left[1])} ({left[0].into_string_lhs()})'
        right_string = descriptive_backend_type(right[1]) + (
            f' ({right[0].into_string_rhs()})'
            if isinstance(right[0], Checkable)
            else ''
        )
        raise NotANumberException() from TypeError(
            f'Housing arithmetic operators expect numeric values: {left_string} {operator.value} {right_string}'
        )


class ConditionFailedExtraInfoException(ExecutionException):
    pass
