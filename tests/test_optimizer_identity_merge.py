"""`lhs = identity; lhs OP rhs` -> `lhs = rhs` for each operator's identity."""

from pyhtsl import Container, PlayerStat

# Increment identity is 0
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 0
    x += y

assert container.into_htsl() == 'var "x" = "%var.player/y 0%L" true', (
    container.into_htsl()
)


# Multiply identity is 1
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 1
    x *= y

assert container.into_htsl() == 'var "x" = "%var.player/y 0%L" true', (
    container.into_htsl()
)


# BitwiseOr identity is 0
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 0
    x |= y

assert container.into_htsl() == 'var "x" = "%var.player/y 0%L" true', (
    container.into_htsl()
)


# BitwiseXor identity is 0
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 0
    x ^= y

assert container.into_htsl() == 'var "x" = "%var.player/y 0%L" true', (
    container.into_htsl()
)


# BitwiseAnd identity is -1 (all bits set)
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = -1
    x &= y

assert container.into_htsl() == 'var "x" = "%var.player/y 0%L" true', (
    container.into_htsl()
)


# Non-identity init -> no merge (constant fold takes over instead)
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 5
    x += 3

assert container.into_htsl() == 'var "x" = 8 true', container.into_htsl()


# A conditional that reads lhs between `lhs = identity` and the OP blocks the
# merge — `is_using_stat` recurses into `ConditionalExpression`'s body. Without
# this, the optimizer would silently rewrite `x = 0; if(c) z = x; x += y`
# into `x = y; if(c) z = x` and the read inside the conditional would observe
# the post-increment value.
from pyhtsl import IfAll  # noqa: E402

with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    z = PlayerStat('z').as_long()
    cond = PlayerStat('cond').as_long()
    x.value = 0
    with IfAll(cond > 0):
        z.value = x
    x += y

expected = (
    'var "x" = 0 true\n'
    'if and (var "cond" > 0 0) {\n'
    '    var "z" = "%var.player/x 0%L" true\n'
    '}\n'
    'var "x" += "%var.player/y 0%L" true'
)
assert container.into_htsl() == expected, container.into_htsl()
