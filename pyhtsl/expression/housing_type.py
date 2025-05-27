from typing import TypeAlias


__all__ = (
    'NumericHousingType',
    'HousingType',
    '_housing_type_as_right_side',
)


NumericHousingType: TypeAlias = int | float
HousingType: TypeAlias = NumericHousingType | str


def _housing_type_as_right_side(value: HousingType) -> str:
    if isinstance(value, NumericHousingType):
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            formatted = f"{value:.15g}"
            if '.' not in formatted:
                formatted += '.0'
            return formatted
    return f'"{value.replace('"', '\\"')}"'
