from pyhtsl import Container, PlayerStat

with Container() as container:
    x = PlayerStat('x')
    x.value = 5

assert container.into_htsl() == 'var "x" = 5 true', container.into_htsl()


with Container() as container:
    x = PlayerStat('with space')
    x.value = 1

assert container.into_htsl() == 'var "with space" = 1 true', container.into_htsl()
