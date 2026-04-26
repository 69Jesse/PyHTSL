from pyhtsl import Container, PlayerStat

with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x += y

assert container.into_htsl() == 'var "x" += "%var.player/y 0%L" true', (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x -= y

assert container.into_htsl() == 'var "x" -= "%var.player/y 0%L" true', (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x *= y

assert container.into_htsl() == 'var "x" *= "%var.player/y 0%L" true', (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_double()
    y = PlayerStat('y').as_double()
    x /= y

assert container.into_htsl() == 'var "x" /= "%var.player/y 0.0%D" true', (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x //= y

assert container.into_htsl() == 'var "x" /= "%var.player/y 0%L" true', (
    container.into_htsl()
)


# Nested expression: x = (a + b) - 1 collapses optimally
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    x = PlayerStat('x').as_long()
    x.value = (a + b) - 1

expected = (
    'var "x" = "%var.player/a 0%L" true\n'
    'var "x" += "%var.player/b 0%L" true\n'
    'var "x" -= 1 true'
)
assert container.into_htsl() == expected, container.into_htsl()
