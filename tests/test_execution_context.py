"""ExecutionContext basics: put/get round-trips, default values, conditional assertions."""

from helpers import expect_exception

from pyhtsl import (
    Container,
    ExecutionContext,
    GlobalStat,
    IfAll,
    PlayerStat,
)
from pyhtsl.execute.backend_type import cast_to_backend_long

# put/get round-trip for long
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, 42)

assert int(ctx.get(x)) == 42, ctx.get(x)


# put/get round-trip for double (use get_raw to avoid the simulator's 3-decimal
# string-rounding when reading doubles back through ctx.get).
with ExecutionContext() as ctx:
    d = PlayerStat('d').as_double()
    ctx.put(d, 3.14159)

assert float(ctx.get_raw(d)) == 3.14159, ctx.get_raw(d)


# put/get round-trip for string
with ExecutionContext() as ctx:
    s = PlayerStat('s').as_string()
    ctx.put(s, 'hello')

assert str(ctx.get(s)) == 'hello', ctx.get(s)


# Stat that wasn't put returns its default fallback (long: 0)
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()

assert int(ctx.get(x)) == 0, ctx.get(x)


# `with_fallback(N)` is honored by both `get` and `get_raw` when the stat hasn't been set
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long().with_fallback(42)

assert int(ctx.get(x)) == 42, ctx.get(x)
assert int(ctx.get_raw(x)) == 42, ctx.get_raw(x)


# `ctx.put` overrides the fallback.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long().with_fallback(42)
    ctx.put(x, 7)

assert int(ctx.get(x)) == 7, ctx.get(x)


# Arithmetic propagates through execution
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 10)
    y.value = x + 5

assert int(ctx.get(y)) == 15, ctx.get(y)


# GlobalStat works in execution too
with ExecutionContext() as ctx:
    g = GlobalStat('shared').as_long()
    ctx.put(g, 7)

assert int(ctx.get(g)) == 7, ctx.get(g)


# Conditional execution: branch is taken when the condition holds
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 10)
    with IfAll(x > 5):
        y.value = 1
    # else: y stays at 0

assert int(ctx.get(y)) == 1, ctx.get(y)


# Conditional execution: branch is skipped when the condition fails
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 1)
    with IfAll(x > 5):
        y.value = 1

assert int(ctx.get(y)) == 0, ctx.get(y)


# Failing assert raises AssertionError that escapes the context manager
with expect_exception(AssertionError):
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        ctx.put(x, 5)
        ctx.assert_all(x == 10)


# assert_any: passes when at least one condition holds
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, 5)
    ctx.assert_any(x == 1, x == 5, x == 99)


# assert_any with a callable that returns None is a no-op (skipped)
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, 5)

    def maybe_check() -> None:
        return None  # callable returns None, condition is discarded

    # Vacuously passes since the only condition is discarded.
    ctx.assert_any(maybe_check, x == 5)


# Sanity: ExecutionContext can also produce HTSL via into_htsl
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1

assert container.into_htsl() == 'var "x" = 1 true', container.into_htsl()


# Storage path: each assignment substitutes the rhs once. Chained-placeholder
# strings stay one level deep when stored (here `c` keeps `%var.player/s0%`,
# not 5). An intentional self-assignment then routes through get()'s fullmatch
# loop, which DOES chase the chain transitively, so c ends up holding the
# resolved numeric value 5.
with ExecutionContext() as ctx:
    s0 = PlayerStat('s0').without_auto_unset()
    s0.value = 5
    a = PlayerStat('a').without_auto_unset()
    a.value = '%var.player/s'
    b = PlayerStat('b').without_auto_unset()
    b.value = 0

    c = PlayerStat('c').without_auto_unset()
    c.value = '%var.player/a%%var.player/b%%'

    # Mid-execution check: at this point c stores the once-substituted
    # placeholder string. get_raw bypasses substitution so we see the literal.
    def check_before_self_assign() -> None:
        assert str(ctx.get_raw(c)) == '%var.player/s0%', ctx.get_raw(c)

    ctx.run(check_before_self_assign)

    # Intentional self-assign: rhs renders as bare `%var.player/c%` (no type
    # suffix because fix_type_compatibility is skipped), and get()'s fullmatch
    # loop chases the placeholder chain `c` -> `%var.player/s0%` -> `s0` -> 5.
    c.set(c, is_intentional_self_assignment=True)

# Emitted HTSL keeps the bare placeholder form for the self-assign.
assert 'var "c" = %var.player/c%' in ctx.into_htsl(), ctx.into_htsl()

# After execution: c now holds the resolved value, not the placeholder.
assert int(ctx.get_raw(c)) == 5, ctx.get_raw(c)


# Stat-to-stat assignment preserves the rhs's native type, but a Python-`str`
# rhs (which renders to HTSL as quoted, `var "c" = "%var.player/a%"`) routes
# through string-mode → substitute → cast, so `c.value = f"{a}"` stores long
# 123 even though `a` is double 123.0.
with ExecutionContext() as ctx:
    a = PlayerStat('a').without_auto_unset()
    a.value = 123.0
    b = PlayerStat('b').without_auto_unset()
    b.value = a
    c = PlayerStat('c').without_auto_unset()
    c.value = f'{a}'

assert 'var "b" = %var.player/a%' in ctx.into_htsl(), ctx.into_htsl()
assert 'var "c" = "%var.player/a%"' in ctx.into_htsl(), ctx.into_htsl()
assert isinstance(ctx.get_raw(b), float), type(ctx.get_raw(b))
assert ctx.get_raw(b) == 123.0, ctx.get_raw(b)
assert isinstance(ctx.get_raw(c), int) and not isinstance(ctx.get_raw(c), bool), type(
    ctx.get_raw(c)
)
assert ctx.get_raw(c) == 123, ctx.get_raw(c)


# === Long precision: matches Java's Long, no float64 round-trip drift ===
#
# Java's `long` is exactly 64 bits. The simulator must round-trip every
# representable long through ctx.get without losing precision — float64 only
# has ~53 bits of mantissa, so anything above 2**53 had been silently
# corrupted before cast_to_backend_long was fixed to try int() first.

# Boundary: exactly 2**53 round-trips cleanly via either path.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, 2**53)

assert int(ctx.get(x)) == 2**53, ctx.get(x)


# Above the float53 line: values that float64 cannot represent exactly.
for _v in (2**53 + 1, 2**60 - 1, 22551026487849030, 9223372036854775807):
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        ctx.put(x, _v)

    got = int(ctx.get(x))
    assert got == _v, f'long round-trip lost precision: got {got}, want {_v}'


# Java long min / max boundaries.
for _v in (-(2**63), 2**63 - 1):
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        ctx.put(x, _v)

    got = int(ctx.get(x))
    assert got == _v, f'long boundary lost precision: got {got}, want {_v}'


# Bitwise ops on large packed longs preserve precision (the use-case that
# motivated the fix — IntStack packs many small ints into one long).
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    # Packed value [70, 60, 50, 40, 30, 20] at 10 bits per slot.
    packed = 70 + 60 * 1024 + 50 * 2**20 + 40 * 2**30 + 30 * 2**40 + 20 * 2**50
    ctx.put(x, packed)
    y.value = x & 1023

assert int(ctx.get(y)) == 70, ctx.get(y)


# Right-shift through the high bits keeps the bit pattern intact.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    ctx.put(x, 1 << 60)
    y.value = x >> 60

assert int(ctx.get(y)) == 1, ctx.get(y)


# Decimal/exponent strings still parse via the float fallback (so existing
# behavior on non-integer literals is preserved).

assert (x := cast_to_backend_long('1.5')) is not None and int(x) == 1
assert (x := cast_to_backend_long('2.9')) is not None and int(x) == 2
assert (x := cast_to_backend_long('1e3')) is not None and int(x) == 1000
assert cast_to_backend_long('garbage') is None
assert (x := cast_to_backend_long('')) is not None and int(x) == 0
assert (x := cast_to_backend_long('1,000')) is not None and int(x) == 1000
# Out-of-range integer string returns None instead of clipping.
assert cast_to_backend_long('9223372036854775808') is None  # 2**63
assert cast_to_backend_long('-9223372036854775809') is None  # -(2**63) - 1
