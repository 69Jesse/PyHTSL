from pyhtsw import Container, GlobalStat

with Container() as container:
    g = GlobalStat('shared').as_long()
    g.value = 42

assert container.into_htsl() == 'globalvar "shared" = 42 true', container.into_htsl()
