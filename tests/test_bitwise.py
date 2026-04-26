from pyhtsl import Container, PlayerStat

with Container() as container:
    x = PlayerStat('x').as_long()
    x &= 0xF

assert container.into_htsl() == 'var "x" &= 15 true', container.into_htsl()


with Container() as container:
    x = PlayerStat('x').as_long()
    x |= 0xF

assert container.into_htsl() == 'var "x" |= 15 true', container.into_htsl()


with Container() as container:
    x = PlayerStat('x').as_long()
    x ^= 5

assert container.into_htsl() == 'var "x" ^= 5 true', container.into_htsl()


with Container() as container:
    x = PlayerStat('x').as_long()
    x <<= 2

assert container.into_htsl() == 'var "x" <<= 2 true', container.into_htsl()


with Container() as container:
    x = PlayerStat('x').as_long()
    x >>= 2

assert container.into_htsl() == 'var "x" >>= 2 true', container.into_htsl()


with Container() as container:
    x = PlayerStat('x').as_long()
    x.logical_rshift(2).write()

assert container.into_htsl() == 'var "x" >>>= 2 true', container.into_htsl()
