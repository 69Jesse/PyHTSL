"""cast_to_long / cast_to_double / cast_to_string emit intentional self-assignments
with the destination type's suffix on the rhs (so HTSL parses through the type
on the way in)."""

from pyhtsl import Container, PlayerStat

# Casting a double-typed stat to long: read x with the long suffix, write back.
with Container() as container:
    x = PlayerStat('x').as_double()
    x.cast_to_long()

assert container.into_htsl() == 'var "x" = "%var.player/x 0%L" true', (
    container.into_htsl()
)


# Casting a long-typed stat to double: read x with the double suffix, write back.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.cast_to_double()

assert container.into_htsl() == 'var "x" = "%var.player/x 0.0%D" true', (
    container.into_htsl()
)


# Casting to string: no type suffix at all on the rhs.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.cast_to_string()

assert container.into_htsl() == 'var "x" = "%var.player/x%" true', container.into_htsl()
