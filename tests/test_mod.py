from pyhtsw import Container, PlayerStat

with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    y.value = x % 3

expected = (
    'var "tmp0" = "%var.player/x 0%L" false\n'
    'var "tmp0" /= 3 false\n'
    'var "tmp0" *= 3 false\n'
    'var "y" = "%var.player/x 0%L" true\n'
    'var "y" -= "%var.player/tmp0 0%L" true\n'
    'if and (var "y" < 0 0) {\n'
    '    var "y" += 3 true\n'
    '}'
)
assert container.into_htsl() == expected, container.into_htsl()
