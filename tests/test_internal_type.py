"""InternalType: type_compatible_housing_type, default_housing_type, from_value."""

from helpers import expect_exception

from pyhtsl.internal_type import InternalType

# Coercion to LONG
assert InternalType.LONG.type_compatible_housing_type(3.0) == 3
assert isinstance(InternalType.LONG.type_compatible_housing_type(3.0), int)
assert InternalType.LONG.type_compatible_housing_type('5') == 5
# Non-integer float can't become LONG
with expect_exception(TypeError):
    InternalType.LONG.type_compatible_housing_type(3.14)


# Coercion to DOUBLE
assert InternalType.DOUBLE.type_compatible_housing_type(3) == 3.0
assert isinstance(InternalType.DOUBLE.type_compatible_housing_type(3), float)


# Coercion to STRING
assert InternalType.STRING.type_compatible_housing_type(5) == '5'


# from_value
assert InternalType.from_value(5) is InternalType.LONG
assert InternalType.from_value(3.14) is InternalType.DOUBLE
assert InternalType.from_value('hi') is InternalType.STRING
