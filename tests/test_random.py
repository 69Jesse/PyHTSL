from pyhtsl import Container, PlayerStat, RandomDecimal, RandomWhole

with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = RandomWhole(1, 10)

assert container.into_htsl() == 'var "x" = "%random.whole/1 10%L" true', (
    container.into_htsl()
)


with Container() as container:
    y = PlayerStat('y').as_double()
    y.value = RandomDecimal(0.0, 1.0)

assert container.into_htsl() == 'var "y" = "%random.decimal/0.0 1.0%D" true', (
    container.into_htsl()
)
