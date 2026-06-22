"""HousingType formatting and parsing primitives."""

from pyhtsw.expression.housing_type import housing_type_as_rhs, housing_type_from_string

# Integers render bare
assert housing_type_as_rhs(5) == '5'
assert housing_type_as_rhs(0) == '0'
assert housing_type_as_rhs(-7) == '-7'

# Floats always carry a decimal point — even integral ones
assert housing_type_as_rhs(3.14) == '3.14'
assert housing_type_as_rhs(2.0) == '2.0'
assert housing_type_as_rhs(0.0) == '0.0'
assert housing_type_as_rhs(0.1) == '0.1'

# Strings get quoted
assert housing_type_as_rhs('hello') == '"hello"'
assert housing_type_as_rhs('') == '""'


# Parse: ints first, then floats, then string
assert housing_type_from_string('5') == 5
assert isinstance(housing_type_from_string('5'), int)

assert housing_type_from_string('3.14') == 3.14
assert isinstance(housing_type_from_string('3.14'), float)

assert housing_type_from_string('hello') == 'hello'
assert isinstance(housing_type_from_string('hello'), str)
