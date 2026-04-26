"""Conditionals nest, with proper indentation."""

from pyhtsl import Container, IfAll, PlayerStat, chat


with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    with IfAll(x > 0):
        with IfAll(y > 0):
            chat('both positive')

expected = (
    'if and (var "x" > 0 0) {\n'
    '    if and (var "y" > 0 0) {\n'
    '        chat "both positive"\n'
    '    }\n'
    '}'
)
assert container.into_htsl() == expected, container.into_htsl()
