from pyhtsl import Container, PlayerStat

with Container() as container:
    s = PlayerStat('name').as_string()
    s.value = 'Alice'

assert container.into_htsl() == 'var "name" = "Alice" true', container.into_htsl()


with Container() as container:
    d = PlayerStat('score').as_double()
    d.value = 3.14

assert container.into_htsl() == 'var "score" = 3.14 true', container.into_htsl()


with Container() as container:
    long = PlayerStat('count').as_long()
    long.value = 100

assert container.into_htsl() == 'var "count" = 100 true', container.into_htsl()


with Container() as container:
    any_typed = PlayerStat('any')
    any_typed.value = 7

assert container.into_htsl() == 'var "any" = 7 true', container.into_htsl()


with Container() as container:
    long = PlayerStat('a').as_long()
    other = PlayerStat('b').as_double()
    # cross-type: assigning long-stat to double-stat reads it via fallback "0"
    other.value = long

assert container.into_htsl() == 'var "b" = "%var.player/a 0.0%D" true', (
    container.into_htsl()
)
