import math

__all__ = (
    'INT64_MIN',
    'INT64_MAX',
    'JavaLong',
    'in_int64_range',
    'add',
    'sub',
    'mul',
    'neg',
    'div',
    'mod',
    'shl',
    'shr',
    'ushr',
    'bit_and',
    'bit_or',
    'bit_xor',
    'from_double',
)

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1
_TWO_64 = 2**64
# `2**63` as a double — the first value too large for a Java long.
_DOUBLE_LIMIT = 2.0**63


def in_int64_range(value: int) -> bool:
    """Whether `value` already fits a signed 64-bit integer without wrapping."""
    return INT64_MIN <= value <= INT64_MAX


class JavaLong(int):
    """A signed 64-bit two's-complement integer, like a JVM `long`."""

    __slots__ = ()

    def __new__(cls, value: int = 0) -> 'JavaLong':
        return super().__new__(cls, ((int(value) + 2**63) % _TWO_64) - 2**63)

    def __repr__(self) -> str:
        return f'JavaLong({int(self)})'


def add(a: int, b: int) -> JavaLong:
    return JavaLong(int(a) + int(b))


def sub(a: int, b: int) -> JavaLong:
    return JavaLong(int(a) - int(b))


def mul(a: int, b: int) -> JavaLong:
    return JavaLong(int(a) * int(b))


def neg(a: int) -> JavaLong:
    return JavaLong(-int(a))


def div(a: int, b: int) -> JavaLong:
    """Java `/`: integer division truncating toward zero. `b` must be nonzero."""
    a, b = int(a), int(b)
    quotient = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        quotient = -quotient
    return JavaLong(quotient)


def mod(a: int, b: int) -> JavaLong:
    """Java `%`: remainder with the sign of the dividend. `b` must be nonzero."""
    a, b = int(a), int(b)
    return JavaLong(a - int(div(a, b)) * b)


def shl(a: int, count: int) -> JavaLong:
    """Java `<<`. The shift count is masked to its low 6 bits."""
    return JavaLong(int(a) << (int(count) & 63))


def shr(a: int, count: int) -> JavaLong:
    """Java `>>`: arithmetic (sign-propagating) right shift, count masked to 6 bits."""
    return JavaLong(int(a) >> (int(count) & 63))


def ushr(a: int, count: int) -> JavaLong:
    """Java `>>>`: logical (zero-filling) right shift, count masked to 6 bits."""
    n = int(count) & 63
    return JavaLong((int(a) & (_TWO_64 - 1)) >> n)


def bit_and(a: int, b: int) -> JavaLong:
    return JavaLong(int(a) & int(b))


def bit_or(a: int, b: int) -> JavaLong:
    return JavaLong(int(a) | int(b))


def bit_xor(a: int, b: int) -> JavaLong:
    return JavaLong(int(a) ^ int(b))


def from_double(value: float) -> JavaLong:
    """Java's `(long) double` narrowing cast.

    NaN becomes 0, values at or beyond the long range clamp to the nearest
    bound, and everything else is truncated toward zero.
    """
    if math.isnan(value):
        return JavaLong(0)
    if value >= _DOUBLE_LIMIT:
        return JavaLong(INT64_MAX)
    if value <= -_DOUBLE_LIMIT:
        return JavaLong(INT64_MIN)
    return JavaLong(math.trunc(value))
