from pyhtsw import Container, TeamStat

with Container() as container:
    t = TeamStat('points', 'red').as_long()
    t.value = 10

assert container.into_htsl() == 'teamvar "points" "red" = 10 true', (
    container.into_htsl()
)


with Container() as container:
    t = TeamStat('total').as_long()
    t.value = 5

assert container.into_htsl() == 'teamvar "total" = 5 true', container.into_htsl()
