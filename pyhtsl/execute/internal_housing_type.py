import numpy as np

from ..expression.housing_type import HousingType

__all__ = (
    'InternalHousingType',
    'into_internal_housing_type',
    'into_housing_type',
    'internal_into_string',
)


type InternalHousingType = np.int64 | np.float64 | str


def into_internal_housing_type(value: HousingType | InternalHousingType) -> InternalHousingType:
    if isinstance(value, int):
        return np.int64(value)
    if isinstance(value, float):
        return np.float64(value)
    return value


def into_housing_type(value: HousingType | InternalHousingType) -> HousingType:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def internal_into_string(value: InternalHousingType) -> str:
    if isinstance(value, np.integer):
        return str(int(value))
    if isinstance(value, np.floating):
        d = float(value)
        if d.is_integer() and abs(d) < 1e15 and d != 0.0:
            return f'{d:.1f}'
        rep = repr(d)
        if 'e' in rep or 'E' in rep:
            return _java_double_tostring(d)
        return rep
    return value


def _java_double_tostring(d: float) -> str:
    """Mimics Java's Double.toString() for scientific notation values."""
    if d == 0.0:
        return '0.0'
    import math
    negative = d < 0
    d = abs(d)
    exp = math.floor(math.log10(d))
    mantissa = d / (10.0 ** exp)
    mantissa_str = f'{mantissa:.17g}'
    if '.' not in mantissa_str:
        mantissa_str += '.0'
    mantissa_str = mantissa_str.rstrip('0')
    if mantissa_str.endswith('.'):
        mantissa_str += '0'
    sign = '-' if negative else ''
    return f'{sign}{mantissa_str}E{exp}'
