"""Operations that are no-ops (e.g. += 0, *= 1) get removed entirely."""

from pyhtsw import Container, PlayerStat

# `+= 0` and `-= 0` are no-ops; only the surviving op remains
with Container() as container:
    x = PlayerStat('x').as_long()
    x += 0
    x += 5
    x -= 0

assert container.into_htsl() == 'var "x" += 5 true', container.into_htsl()


# `*= 1`, `/= 1` are no-ops
with Container() as container:
    x = PlayerStat('x').as_long()
    x *= 1
    x *= 2
    x //= 1

assert container.into_htsl() == 'var "x" *= 2 true', container.into_htsl()


# Bitwise / shift no-ops
with Container() as container:
    x = PlayerStat('x').as_long()
    x |= 0
    x ^= 0
    x <<= 0
    x >>= 0
    x += 1

assert container.into_htsl() == 'var "x" += 1 true', container.into_htsl()


# Self-set with non-intentional flag is removed
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = x

assert container.into_htsl() == '', container.into_htsl()
