from pyhtsl import Container, PlayerStat

with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    x += 2

assert container.into_htsl() == 'var "x" = 3 true', container.into_htsl()
