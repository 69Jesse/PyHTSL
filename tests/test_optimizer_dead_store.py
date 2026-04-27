"""A write to lhs is dead if the next expression that touches lhs fully overwrites it."""

from pyhtsl import Container, PlayerStat

# Set followed by Set: first is dead
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 5
    x.value = 10

assert container.into_htsl() == 'var "x" = 10 true', container.into_htsl()


# Increment followed by Set: increment is dead (its result is overwritten without read)
with Container() as container:
    x = PlayerStat('x').as_long()
    x += 100
    x.value = 5

assert container.into_htsl() == 'var "x" = 5 true', container.into_htsl()


# Multiply followed by Set: also dead
with Container() as container:
    x = PlayerStat('x').as_long()
    x *= 7
    x.value = 5

assert container.into_htsl() == 'var "x" = 5 true', container.into_htsl()


# A read in between blocks the elimination
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 5
    y.value = x  # reads x; the earlier x = 5 is now alive
    x.value = 10

expected = 'var "x" = 5 true\nvar "y" = "%var.player/x 0%L" true\nvar "x" = 10 true'
assert container.into_htsl() == expected, container.into_htsl()


# Self-reference in the overwrite blocks elimination (rhs reads lhs)
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 5
    x.value = x  # reads x; first assignment is alive

# Self-assignment after the optimizer/dead-store phase is removed by no-op pass
# (`stat = stat`). What's left is the only meaningful expression: x = 5.
assert container.into_htsl() == 'var "x" = 5 true', container.into_htsl()


# A conditional that reads lhs in its body counts as a "use" — `is_using_stat`
# recurses into `ConditionalExpression.if_expressions` / `else_expressions`.
# Without this, `x = 5` would be wrongly eliminated even though the conditional
# reads (and writes) x.
from pyhtsl import IfAll  # noqa: E402

with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 5
    with IfAll(y > 0):
        x += 1
    x.value = 10

expected = (
    'var "x" = 5 true\n'
    'if and (var "y" > 0 0) {\n'
    '    var "x" += 1 true\n'
    '}\n'
    'var "x" = 10 true'
)
assert container.into_htsl() == expected, container.into_htsl()


# A stat referenced via its rendered placeholder inside a string field also
# counts as a "use". `chat(f"...{x}...")` embeds `%var.player/x ...%` in the
# expression's `line` attribute; without scanning string fields,
# `is_using_stat` would miss it and the dead-store optimizer would wrongly
# eliminate the prior `x = 5`.
from pyhtsl import chat  # noqa: E402

with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 5
    chat(f'value is {x}')
    x.value = 10

expected = 'var "x" = 5 true\nchat "value is %var.player/x 0%"\nvar "x" = 10 true'
assert container.into_htsl() == expected, container.into_htsl()
