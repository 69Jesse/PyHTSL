import math

import numpy as np

from ..expression.housing_type import HousingType
from ..internal_type import InternalType
from .java_long import INT64_MAX, INT64_MIN, JavaLong

__all__ = (
    'BackendType',
    'JavaLong',
    'into_backend_type',
    'into_housing_type',
    'backend_into_string',
    'backend_matches_internal_type',
    'cast_to_backend_long',
    'cast_to_backend_double',
    'backend_to_default_backend',
    'is_default_backend',
)


type BackendType = JavaLong | np.float64 | str


def into_backend_type(value: HousingType | BackendType) -> BackendType:
    if isinstance(value, int):
        return JavaLong(value)
    if isinstance(value, float):
        return np.float64(value)
    return value


def into_housing_type(value: HousingType | BackendType) -> HousingType:
    if isinstance(value, JavaLong):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def backend_into_string(value: BackendType) -> str:
    if isinstance(value, JavaLong):
        return f'{int(value):,}'
    if isinstance(value, np.floating):
        d = float(value)
        if d.is_integer() and abs(d) < 1e15:
            return f'{int(d):,}'
        rep = repr(d)
        if 'e' in rep or 'E' in rep:
            return _java_double_tostring(d)
        rounded = round(d, 3)
        result = f'{rounded:,.3f}'.rstrip('0').rstrip('.')
        return result
    return value


def _java_double_tostring(d: float) -> str:
    """Mimics Java's Double.toString() for scientific notation values."""
    if d == 0.0:
        return '0.0'
    negative = d < 0
    d = abs(d)
    exp = math.floor(math.log10(d))
    mantissa = d / (10.0**exp)
    mantissa_str = f'{mantissa:.17g}'
    if '.' not in mantissa_str:
        mantissa_str += '.0'
    mantissa_str = mantissa_str.rstrip('0')
    if mantissa_str.endswith('.'):
        mantissa_str += '0'
    sign = '-' if negative else ''
    return f'{sign}{mantissa_str}E{exp}'


def backend_matches_internal_type(
    value: BackendType,
    internal_type: InternalType,
) -> bool:
    if internal_type is InternalType.ANY:
        return True
    if internal_type is InternalType.LONG:
        return isinstance(value, JavaLong)
    if internal_type is InternalType.DOUBLE:
        return isinstance(value, np.floating)
    if internal_type is InternalType.STRING:
        return isinstance(value, str)
    return False


def cast_to_backend_long(value: str) -> JavaLong | None:
    if not value:
        return JavaLong(0)
    cleaned = value.replace(',', '')
    try:
        n = int(cleaned)
    except ValueError:
        try:
            n = int(np.float64(cleaned))
        except (ValueError, ArithmeticError):
            return None
    if n < INT64_MIN or n > INT64_MAX:
        return None
    return JavaLong(n)


def cast_to_backend_double(value: str) -> np.float64 | None:
    if not value:
        return np.float64(0.0)
    cleaned = value.replace(',', '')
    try:
        return np.float64(cleaned)
    except (ValueError, ArithmeticError):
        return None


def backend_to_default_backend(value: BackendType) -> BackendType:
    if isinstance(value, JavaLong):
        return JavaLong(0)
    if isinstance(value, np.floating):
        return np.float64(0.0)
    return ''


def is_default_backend(value: BackendType) -> bool:
    return value == backend_to_default_backend(value)
