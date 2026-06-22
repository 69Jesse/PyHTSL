"""auto_unset controls the trailing `true`/`false` flag on stat assignments."""

from pyhtsw import Container, PlayerStat

with Container() as container:
    x = PlayerStat('x', auto_unset=True)
    x.value = 5

assert container.into_htsl() == 'var "x" = 5 true', container.into_htsl()


with Container() as container:
    x = PlayerStat('x', auto_unset=False)
    x.value = 5

assert container.into_htsl() == 'var "x" = 5 false', container.into_htsl()


# Mixed in a single block
with Container() as container:
    a = PlayerStat('a', auto_unset=True)
    b = PlayerStat('b', auto_unset=False)
    a.value = 1
    b.value = 2

expected = 'var "a" = 1 true\nvar "b" = 2 false'
assert container.into_htsl() == expected, container.into_htsl()
