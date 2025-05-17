import numpy as np

from typing import TypeAlias


__all__ = (
    'NumericHousingType',
    'HousingType',
    '_housing_type_as_right_side',
)


NumericHousingType: TypeAlias = int | float
HousingType: TypeAlias = NumericHousingType | str


def _housing_type_as_right_side(self: HousingType) -> str:
    if isinstance(self, NumericHousingType):
        if isinstance(self, int):
            return str(self)
        elif isinstance(self, float):
            return np.format_float_positional(self, trim='-')
    return f'"{self.replace('"', '\\"')}"'
