"""cast_to_long / cast_to_double / cast_to_string emit intentional self-assignments."""

from pyhtsl import Container, PlayerStat


with Container() as container:
    x = PlayerStat('x').as_double()
    x.cast_to_long()

# The cast reads x as the source type and assigns back. Because it's marked
# as an intentional self-assignment it survives the no-op pass.
assert (
    container.into_htsl() == 'var "x" = "%var.player/x 0.0%D" true'
), container.into_htsl()


with Container() as container:
    x = PlayerStat('x').as_long()
    x.cast_to_double()

assert (
    container.into_htsl() == 'var "x" = "%var.player/x 0%L" true'
), container.into_htsl()
