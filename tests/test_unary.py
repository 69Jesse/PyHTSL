from pyhtsl import Container, PlayerStat

with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    y.value = -x

expected = 'var "y" = "%var.player/x 0%L" true\nvar "y" *= -1 true'
assert container.into_htsl() == expected, container.into_htsl()


# abs: long input
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    y.value = abs(x)

expected = (
    'var "y" = "%var.player/x 0%L" true\n'
    'if and (var "y" < 0 0) {\n'
    '    var "y" *= -1 true\n'
    '}'
)
assert container.into_htsl() == expected, container.into_htsl()


# abs: double input
with Container() as container:
    x = PlayerStat('x').as_double()
    y = PlayerStat('y').as_double()
    y.value = abs(x)

expected = (
    'var "y" = "%var.player/x 0.0%D" true\n'
    'if and (var "y" < 0.0 0.0) {\n'
    '    var "y" *= -1.0 true\n'
    '}'
)
assert container.into_htsl() == expected, container.into_htsl()
