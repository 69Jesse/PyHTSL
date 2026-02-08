from enum import Enum
from typing import TYPE_CHECKING

from .expression.housing_type import HousingType

if TYPE_CHECKING:
    from .checkable import Checkable


__all__ = ('InternalType',)


class InternalType(Enum):
    ANY = 0
    LONG = 1
    DOUBLE = 2
    STRING = 3

    def default_housing_type(self) -> HousingType | None:
        if self is InternalType.ANY:
            return None
        elif self is InternalType.LONG:
            return 0
        elif self is InternalType.DOUBLE:
            return 0.0
        elif self is InternalType.STRING:
            return ''
        else:
            raise TypeError(f'Unsupported internal type: {self}')

    def type_compatible_housing_type(self, value: HousingType) -> HousingType:
        try:
            if self is InternalType.ANY:
                return value
            elif self is InternalType.LONG:
                return int(value)
            elif self is InternalType.DOUBLE:
                return float(value)
            elif self is InternalType.STRING:
                return str(value)
            else:
                raise TypeError(f'Unsupported internal type: {self}')
        except (ValueError, TypeError) as exc:
            raise TypeError(
                f'Cannot transform value {repr(value)} to internal type {self.name}.'
            ) from exc

    @staticmethod
    def from_value(value: 'Checkable | HousingType') -> 'InternalType':
        if isinstance(value, str):
            return InternalType.STRING
        elif isinstance(value, int):
            return InternalType.LONG
        elif isinstance(value, float):
            return InternalType.DOUBLE

        return value.internal_type
