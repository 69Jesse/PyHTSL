from typing import TypeAlias


__all__ = (
    'NumericHousingType',
    'HousingType',
)


NumericHousingType: TypeAlias = int | float
HousingType: TypeAlias = NumericHousingType | str
