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
