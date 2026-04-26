from pyhtsl import Container, Else, IfAll, IfAny, PlayerStat, chat

# IfAll with multiple conditions
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    with IfAll(x > 0, y < 10):
        chat('both')

assert container.into_htsl() == (
    'if and (var "x" > 0 0, var "y" < 10 0) {\n    chat "both"\n}'
), container.into_htsl()


# IfAny: at least one
with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAny(x == 1, x == 2):
        chat('one or two')

assert container.into_htsl() == (
    'if or (var "x" == 1 0, var "x" == 2 0) {\n    chat "one or two"\n}'
), container.into_htsl()


# Else
with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x > 0):
        chat('positive')
    with Else:
        chat('not positive')

assert container.into_htsl() == (
    'if and (var "x" > 0 0) {\n'
    '    chat "positive"\n'
    '} else {\n'
    '    chat "not positive"\n'
    '}'
), container.into_htsl()


# IfAny with no conditions and all_if_no_conditions=True (default) -> "and ()"
with Container() as container:
    with IfAny():
        chat('always')

assert container.into_htsl() == ('if and () {\n    chat "always"\n}'), (
    container.into_htsl()
)


# IfAny with no conditions and all_if_no_conditions=False -> "or ()"
with Container() as container:
    with IfAny(all_if_no_conditions=False):
        chat('never')

assert container.into_htsl() == ('if or () {\n    chat "never"\n}'), (
    container.into_htsl()
)


# Else without preceding If raises
with Container():
    raised = False
    try:
        with Else:
            chat('orphan')
    except SyntaxError:
        raised = True
    assert raised, 'expected SyntaxError for orphan Else'
