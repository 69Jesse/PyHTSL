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
        return str(self)
    return f'"{self.replace('"', '\\"')}"'
