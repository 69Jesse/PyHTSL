"""Optimizations must not move stat reads/writes across an execution barrier.

A `pause` yields back to the housing tick loop and a triggered `function` runs
other code; across either, another script can observe — or change — a stat. So
a write that is "overwritten anyway" later is *not* dead if a barrier sits
between the two writes, and two writes around a barrier may not be merged: in
the meantime the value could have been read or changed.

A barrier nested inside a `random` or `if` block still counts — it is
reachable, so the conservative choice keeps the earlier write.
"""

from pyhtsl import (
    Container,
    IfAll,
    PlayerStat,
    Random,
    pause_execution,
    trigger_function,
)
from pyhtsl.actions.pause_execution import PauseExecutionExpression
from pyhtsl.expression.binary_expression import BinaryExpression, BinaryOperator
from pyhtsl.internal_type import InternalType
from pyhtsl.stats.temporary_stat import TemporaryStat

# --- Dead-store elimination ------------------------------------------------

# The motivating case: a pause *and* a triggered function between the two
# writes. `x = 1` must survive — both barriers can observe it.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    pause_execution(1)
    trigger_function('hello')
    x.value = 2

expected = 'var "x" = 1 true\npause 1\nfunction "hello" false\nvar "x" = 2 true'
assert container.into_htsl() == expected, container.into_htsl()


# A pause alone blocks elimination.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    pause_execution(1)
    x.value = 2

expected = 'var "x" = 1 true\npause 1\nvar "x" = 2 true'
assert container.into_htsl() == expected, container.into_htsl()


# A triggered function alone blocks elimination.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    trigger_function('hello')
    x.value = 2

expected = 'var "x" = 1 true\nfunction "hello" false\nvar "x" = 2 true'
assert container.into_htsl() == expected, container.into_htsl()


# A pause nested inside a `random` block still counts — it is reachable.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    with Random:
        pause_execution(1)
    x.value = 2

expected = 'var "x" = 1 true\nrandom {\n    pause 1\n}\nvar "x" = 2 true'
assert container.into_htsl() == expected, container.into_htsl()


# A triggered function nested inside an `if` block still counts.
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 1
    with IfAll(y > 0):
        trigger_function('hello')
    x.value = 2

expected = (
    'var "x" = 1 true\n'
    'if and (var "y" > 0 0) {\n'
    '    function "hello" false\n'
    '}\n'
    'var "x" = 2 true'
)
assert container.into_htsl() == expected, container.into_htsl()


# Control: no barrier between the writes — the first is still eliminated.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    x.value = 2

assert container.into_htsl() == 'var "x" = 2 true', container.into_htsl()


# A barrier *after* the overwrite does not save the dead store — nothing
# observes `x` between the two writes.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    x.value = 2
    pause_execution(1)

assert container.into_htsl() == 'var "x" = 2 true\npause 1', container.into_htsl()


# The barrier only blocks elimination *across* it: `x = 1` survives the pause,
# but `x += 5` (after the pause, before the overwrite, with nothing observing
# `x` in between) is still dead.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1
    pause_execution(1)
    x += 5
    x.value = 2

expected = 'var "x" = 1 true\npause 1\nvar "x" = 2 true'
assert container.into_htsl() == expected, container.into_htsl()


# --- Identity-set merge ----------------------------------------------------

# `x = 0; x += y` would normally collapse to `x = y`. A pause in between
# blocks it — `x` is observable as `0` at the pause.
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 0
    pause_execution(1)
    x += y

expected = 'var "x" = 0 true\npause 1\nvar "x" += "%var.player/y 0%L" true'
assert container.into_htsl() == expected, container.into_htsl()


# A triggered function blocks the identity merge too.
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    x.value = 0
    trigger_function('hello')
    x += y

expected = (
    'var "x" = 0 true\nfunction "hello" false\nvar "x" += "%var.player/y 0%L" true'
)
assert container.into_htsl() == expected, container.into_htsl()


# --- Temp-stat merge -------------------------------------------------------

# `tmp = a; tmp += b; x = tmp` normally merges into `x = a; x += b`, folding
# the temp away. A barrier between the temp's computation and the read into
# `x` blocks that: the merge would write `x` before the barrier.
a = PlayerStat('a').as_long()
b = PlayerStat('b').as_long()
x = PlayerStat('x').as_long()

tmp = TemporaryStat(InternalType.LONG)
expressions = [
    BinaryExpression(left=tmp, right=a, operator=BinaryOperator.Set),
    BinaryExpression(left=tmp, right=b, operator=BinaryOperator.Increment),
    PauseExecutionExpression(ticks=1),
    BinaryExpression(left=x, right=tmp, operator=BinaryOperator.Set),
]
BinaryExpression.optimize_binary_expressions(expressions)

assert len(expressions) == 4, expressions
assert isinstance(expressions[2], PauseExecutionExpression), expressions
last = expressions[-1]
assert (
    isinstance(last, BinaryExpression)
    and isinstance(last.right, TemporaryStat)
    and last.left.is_same_stat(x)
), expressions


# Control: the same shape without a barrier *does* merge the temp away.
tmp = TemporaryStat(InternalType.LONG)
expressions = [
    BinaryExpression(left=tmp, right=a, operator=BinaryOperator.Set),
    BinaryExpression(left=tmp, right=b, operator=BinaryOperator.Increment),
    BinaryExpression(left=x, right=tmp, operator=BinaryOperator.Set),
]
BinaryExpression.optimize_binary_expressions(expressions)

assert len(expressions) == 2, expressions
assert all(
    isinstance(expr, BinaryExpression) and expr.left.is_same_stat(x)
    for expr in expressions
), expressions
