from pyhtsw import Container, IfAll, PlayerStat, chat

# Each comparison operator inside IfAll
with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x == 5):
        chat('eq')

assert container.into_htsl() == ('if and (var "x" == 5 0) {\n    chat "eq"\n}'), (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x != 5):
        chat('ne')

assert container.into_htsl() == ('if and (!var "x" == 5 0) {\n    chat "ne"\n}'), (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x > 0):
        chat('gt')

assert container.into_htsl() == ('if and (var "x" > 0 0) {\n    chat "gt"\n}'), (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x < 0):
        chat('lt')

assert container.into_htsl() == ('if and (var "x" < 0 0) {\n    chat "lt"\n}'), (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x >= 5):
        chat('ge')

assert container.into_htsl() == ('if and (var "x" >= 5 0) {\n    chat "ge"\n}'), (
    container.into_htsl()
)


with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x <= 5):
        chat('le')

assert container.into_htsl() == ('if and (var "x" <= 5 0) {\n    chat "le"\n}'), (
    container.into_htsl()
)
