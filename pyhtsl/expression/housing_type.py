import numpy as np

__all__ = (
    'NumericHousingType',
    'HousingType',
    'housing_type_as_rhs',
    'housing_type_from_string',
)


NumericHousingType = int | float
HousingType = NumericHousingType | str


def housing_type_as_rhs(value: HousingType) -> str:
    if isinstance(value, NumericHousingType):
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            formatted = np.format_float_positional(value, trim='-')
            if '.' not in formatted:
                formatted += '.0'
            return formatted
    return f'"{value}"'


def housing_type_from_string(value: str) -> HousingType:
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value
