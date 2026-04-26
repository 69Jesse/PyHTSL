from pyhtsl import Container, PlayerStat


# x ** 0 -> integer 1, no expressions written
with Container() as container:
    x = PlayerStat('x').as_long()
    result = x ** 0

assert result == 1
assert container.into_htsl() == ''


# x ** 1 -> x itself, no expressions written when not assigned
with Container() as container:
    x = PlayerStat('x').as_long()
    result = x ** 1

assert result is x


# x ** 2 -> square via self-multiply
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    y.value = x ** 2

expected = (
    'var "y" = "%var.player/x 0%L" true\n'
    'var "y" *= "%var.player/y 0%L" true'
)
assert container.into_htsl() == expected, container.into_htsl()


# x ** 3 -> square then multiply by x (odd exponent)
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    y.value = x ** 3

expected = (
    'var "y" = "%var.player/x 0%L" true\n'
    'var "y" *= "%var.player/y 0%L" true\n'
    'var "y" *= "%var.player/x 0%L" true'
)
assert container.into_htsl() == expected, container.into_htsl()


# x ** 4 -> square twice
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    y.value = x ** 4

expected = (
    'var "y" = "%var.player/x 0%L" true\n'
    'var "y" *= "%var.player/y 0%L" true\n'
    'var "y" *= "%var.player/y 0%L" true'
)
assert container.into_htsl() == expected, container.into_htsl()


# Negative exponent must raise
with Container():
    x = PlayerStat('x').as_long()
    raised = False
    try:
        x ** -1
    except ValueError:
        raised = True
    assert raised, 'expected ValueError for negative exponent'
