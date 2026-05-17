"""Nested if/else/random blocks aren't valid HTSL — entering one should raise SyntaxError.

ExecutionContext exposes ``allow_nested_expressions`` to bypass this check during simulation.
Entering a Random/If/Else inside a function block (a Block scope, not an expression scope)
must still be allowed: only nested *expression* blocks are rejected.
"""

from helpers import expect_exception

import pyhtsl.container
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


# ExecutionContext with allow_nested_expressions=False (default) still raises
with expect_exception(SyntaxError):
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        ctx.put(x, 10, ignore_warning=True)
        with IfAll(x > 0):
            with IfAll(x > 5):
                chat('nope')


# ExecutionContext with allow_nested_expressions=True bypasses the check
with ExecutionContext(allow_nested_expressions=True) as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 10, ignore_warning=True)
    with IfAll(x > 0):
        with IfAll(x > 5):
            y.value = 1

assert int(ctx.get(y)) == 1, ctx.get(y)


# A `run_right_now=True` function runs its callback synchronously, at decoration
# time. Defining one inside an open IfAll must still give the function body a
# fresh nesting scope: an IfAll inside that body is its own HTSL block, so it is
# legal even though the outer IfAll is still open on the context stack.
with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x > 0):

        @create_function('rrn inner', run_right_now=True)
        def rrn_inner() -> None:
            with IfAll(x > 5):
                chat('legal inside run_right_now function')

        chat('then')

# Just check it didn't raise; render it for good measure.
container.into_htsl()


# ...but a genuine IfAll-inside-IfAll *within* that function body still raises:
# the fresh scope resets nesting at the function boundary, not inside it.
with expect_exception(SyntaxError):
    with Container():
        x = PlayerStat('x').as_long()
        with IfAll(x > 0):

            @create_function('rrn bad', run_right_now=True)
            def rrn_bad() -> None:
                with IfAll(x > 5):
                    with IfAll(x > 10):
                        chat('nope')


# A function callback that raises must not corrupt the container stack: the
# block is marked as run even on failure (so finalize does not run it again and
# re-raise), and the container is always popped off the stack on exit.
_depth_before = len(pyhtsl.container.CONTAINERS)
with expect_exception(SyntaxError):
    with Container():
        x = PlayerStat('x').as_long()

        @create_function('raising body', run_right_now=True)
        def raising_body() -> None:
            with IfAll(x > 0):
                with IfAll(x > 1):
                    chat('nope')


assert len(pyhtsl.container.CONTAINERS) == _depth_before, pyhtsl.container.CONTAINERS
