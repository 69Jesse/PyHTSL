import numpy as np
from typing import TypeAlias


__all__ = (
    'NumericHousingType',
    'HousingType',
    'housing_type_as_right_side',
)


NumericHousingType: TypeAlias = int | float
HousingType: TypeAlias = NumericHousingType | str


def housing_type_as_right_side(value: HousingType) -> str:
    if isinstance(value, NumericHousingType):
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            formatted = np.format_float_positional(value, trim='-')
            if '.' not in formatted:
                formatted += '.0'
            return formatted
    return f'"{value}"'
