"""Nested if/else/random blocks aren't valid HTSL — entering one should raise SyntaxError.

ExecutionContext exposes ``allow_nested_blocks`` to bypass this check during simulation.
Entering a Random/If/Else inside a function block (a Block scope, not an expression scope)
must still be allowed: only nested *expression* blocks are rejected.
"""

from helpers import expect_exception

from pyhtsl import (
    Container,
    Else,
    ExecutionContext,
    IfAll,
    IfAny,
    PlayerStat,
    Random,
    chat,
    create_function,
)

# IfAll inside IfAll raises
with expect_exception(SyntaxError):
    with Container():
        x = PlayerStat('x').as_long()
        with IfAll(x > 0):
            with IfAll(x > 1):
                chat('nope')


# IfAny inside IfAll raises
with expect_exception(SyntaxError):
    with Container():
        x = PlayerStat('x').as_long()
        with IfAll(x > 0):
            with IfAny(x == 1, x == 2):
                chat('nope')


# Random inside IfAll raises
with expect_exception(SyntaxError):
    with Container():
        x = PlayerStat('x').as_long()
        with IfAll(x > 0):
            with Random:
                chat('nope')


# IfAll inside Random raises
with expect_exception(SyntaxError):
    with Container():
        with Random:
            x = PlayerStat('x').as_long()
            with IfAll(x > 0):
                chat('nope')


# Random inside Random raises
with expect_exception(SyntaxError):
    with Container():
        with Random:
            with Random:
                chat('nope')


# IfAll inside the Else branch of an outer If raises
with expect_exception(SyntaxError):
    with Container():
        x = PlayerStat('x').as_long()
        with IfAll(x > 0):
            chat('then')
        with Else:
            with IfAll(x < 0):
                chat('nope')


# Sibling If + Else at the top level still works
with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x > 0):
        chat('then')
    with Else:
        chat('otherwise')

assert container.into_htsl() == (
    'if and (var "x" > 0 0) {\n    chat "then"\n} else {\n    chat "otherwise"\n}'
), container.into_htsl()


# A function body starts a fresh nesting scope: an If inside a function defined
# inside an outer If is fine, because the function body is a Block, not an
# expression-level nested scope.
with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x > 0):

        @create_function('inner')
        def inner() -> None:
            with IfAll(x > 5):
                chat('deep but legal')

        chat('then')

# Just check it didn't raise; render it for good measure.
container.into_htsl()


# ExecutionContext with allow_nested_blocks=False (default) still raises
with expect_exception(SyntaxError):
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        ctx.put(x, 10, ignore_warning=True)
        with IfAll(x > 0):
            with IfAll(x > 5):
                chat('nope')


# ExecutionContext with allow_nested_blocks=True bypasses the check
with ExecutionContext(allow_nested_blocks=True) as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 10, ignore_warning=True)
    with IfAll(x > 0):
        with IfAll(x > 5):
            y.value = 1

assert int(ctx.get(y)) == 1, ctx.get(y)
