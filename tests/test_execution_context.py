"""ExecutionContext basics: put/get round-trips, default values, conditional assertions."""

from pyhtsl import (
    Container,
    ExecutionContext,
    GlobalStat,
    IfAll,
    PlayerStat,
)

# put/get round-trip for long
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, 42)

    def check() -> None:
        assert int(ctx.get(x)) == 42, ctx.get(x)

    ctx.assert_all(check)


# put/get round-trip for double (use get_raw to avoid the simulator's 3-decimal
# string-rounding when reading doubles back through ctx.get).
with ExecutionContext() as ctx:
    d = PlayerStat('d').as_double()
    ctx.put(d, 3.14159)

    def check() -> None:
        assert float(ctx.get_raw(d)) == 3.14159, ctx.get_raw(d)

    ctx.assert_all(check)


# put/get round-trip for string
with ExecutionContext() as ctx:
    s = PlayerStat('s').as_string()
    ctx.put(s, 'hello')

    def check() -> None:
        assert str(ctx.get(s)) == 'hello', ctx.get(s)

    ctx.assert_all(check)


# Stat that wasn't put returns its default fallback (long: 0)
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()

    def check() -> None:
        assert int(ctx.get(x)) == 0, ctx.get(x)

    ctx.assert_all(check)


# `with_fallback(N)` is honored by both `get` and `get_raw` when the stat hasn't
# been put — mirrors HTSL's `%var.player/x N%` semantics.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long().with_fallback(42)

    def check() -> None:
        assert int(ctx.get(x)) == 42, ctx.get(x)
        assert int(ctx.get_raw(x)) == 42, ctx.get_raw(x)

    ctx.assert_all(check)


# `ctx.put` overrides the fallback.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long().with_fallback(42)
    ctx.put(x, 7)

    def check() -> None:
        assert int(ctx.get(x)) == 7, ctx.get(x)

    ctx.assert_all(check)


# Arithmetic propagates through execution
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 10)
    y.value = x + 5

    def check() -> None:
        assert int(ctx.get(y)) == 15, ctx.get(y)

    ctx.assert_all(check)


# GlobalStat works in execution too
with ExecutionContext() as ctx:
    g = GlobalStat('shared').as_long()
    ctx.put(g, 7)

    def check() -> None:
        assert int(ctx.get(g)) == 7, ctx.get(g)

    ctx.assert_all(check)


# Conditional execution: branch is taken when the condition holds
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 10)
    with IfAll(x > 5):
        y.value = 1
    # else: y stays at 0

    def check() -> None:
        assert int(ctx.get(y)) == 1, ctx.get(y)

    ctx.assert_all(check)


# Conditional execution: branch is skipped when the condition fails
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 1)
    with IfAll(x > 5):
        y.value = 1

    def check() -> None:
        assert int(ctx.get(y)) == 0, ctx.get(y)

    ctx.assert_all(check)


# Failing assert raises AssertionError that escapes the context manager
raised = False
try:
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        ctx.put(x, 5)
        ctx.assert_all(x == 10)
except AssertionError:
    raised = True
assert raised, 'expected the failing assert_all to raise AssertionError'


# assert_any: passes when at least one condition holds
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, 5)
    ctx.assert_any(x == 1, x == 5, x == 99)


# assert_any with a callable that returns None is a no-op (skipped)
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, 5)

    def maybe_check() -> None:  # type: ignore[no-untyped-def]
        return None  # callable returns None, condition is discarded

    # Vacuously passes since the only condition is discarded.
    ctx.assert_any(maybe_check, x == 5)


# Sanity: ExecutionContext can also produce HTSL via into_htsl
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1

assert container.into_htsl() == 'var "x" = 1 true', container.into_htsl()
