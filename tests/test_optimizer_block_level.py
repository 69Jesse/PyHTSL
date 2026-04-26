"""Optimizations apply across user-level statements within a block, not just inside a single expression."""

from pyhtsl import Container, PlayerStat


# Adjacent inc/dec across statements collapse
with Container() as container:
    x = PlayerStat('x').as_long()
    x += 5
    x += 3
    x -= 2

assert container.into_htsl() == 'var "x" += 6 true', container.into_htsl()


# Multiplies fold
with Container() as container:
    x = PlayerStat('x').as_long()
    x *= 2
    x *= 3
    x *= 4

assert container.into_htsl() == 'var "x" *= 24 true', container.into_htsl()


# Set + ops collapse all the way to a single Set
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    x += 2
    x *= 3
    x -= 1

# 1 -> 3 -> 9 -> 8
assert container.into_htsl() == 'var "x" = 8 true', container.into_htsl()


# Bitwise constant ops fold
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 0xF0
    x |= 0x0F
    x ^= 0x33
    x <<= 1

# 0xF0 | 0x0F = 0xFF; 0xFF ^ 0x33 = 0xCC; 0xCC << 1 = 0x198 = 408
assert container.into_htsl() == 'var "x" = 408 true', container.into_htsl()


# sum((a, b, c)) at block level collapses to a chain on the destination stat
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    c = PlayerStat('c').as_long()
    result = PlayerStat('result').as_long()
    result.value = sum((a, b, c))

expected = (
    'var "result" = "%var.player/a 0%L" true\n'
    'var "result" += "%var.player/b 0%L" true\n'
    'var "result" += "%var.player/c 0%L" true'
)
assert container.into_htsl() == expected, container.into_htsl()


# An unrelated statement between two same-stat ops blocks the fold (because the
# in-between expression reads x). The fold gates on "lhs not used between".
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x += 5
    y.value = x  # reads x
    x += 3

expected = (
    'var "x" += 5 true\n'
    'var "y" = "%var.player/x 0%L" true\n'
    'var "x" += 3 true'
)
assert container.into_htsl() == expected, container.into_htsl()
