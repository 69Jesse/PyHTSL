from pyhtsl import Container, PlayerStat


with Container() as container:
    x = PlayerStat('x').as_long().with_fallback(42)
    y = PlayerStat('y').as_long()
    y.value = x

assert (
    container.into_htsl() == 'var "y" = "%var.player/x 42%L" true'
), container.into_htsl()


with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    y.value = x

assert (
    container.into_htsl() == 'var "y" = "%var.player/x 0%L" true'
), container.into_htsl()
