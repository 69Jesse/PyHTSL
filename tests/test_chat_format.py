from pyhtsl import Container, GlobalStat, PlayerStat, TeamStat, chat

# f-string with stat references inlines the placeholder
with Container() as container:
    x = PlayerStat('score')
    chat(f'You have {x} points')

assert container.into_htsl() == 'chat "You have %var.player/score% points"', (
    container.into_htsl()
)


with Container() as container:
    g = GlobalStat('shared')
    chat(f'Total: {g}')

assert container.into_htsl() == 'chat "Total: %var.global/shared%"', (
    container.into_htsl()
)


with Container() as container:
    t = TeamStat('points', 'red')
    chat(f'Red: {t}')

assert container.into_htsl() == 'chat "Red: %var.team/points red%"', (
    container.into_htsl()
)
