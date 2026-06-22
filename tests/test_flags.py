"""Scope flags that change rendering / execution semantics:

- `NoTypeCasting`: renders rhs bare (no quotes, no L/D suffix), and the
  simulator skips the string-mode cast pipeline so reads keep the source type.
- `NoFallbackValues`: drops the fallback portion (` 0`, ` 0.0`) inside
  placeholders.
- `NoOptimization`: skips the peephole optimizer so source order is preserved.
"""

from pyhtsw import (
    Container,
    ExecutionContext,
    NoFallbackValues,
    NoOptimization,
    NoTypeCasting,
    PlayerStat,
)

# NoTypeCasting, Stat-to-Stat: typed rhs renders bare with the fallback still
# in the placeholder (compare to the default, which would be `"%var.player/a 0%L"`).
with NoTypeCasting():
    with Container() as container:
        a = PlayerStat('a').as_long()
        b = PlayerStat('b').as_long()
        b.value = a
    htsl = container.into_htsl()

assert htsl == 'var "b" = %var.player/a 0% true', htsl


# NoTypeCasting, Python-`str` placeholder rhs: same bare form. Without the
# flag this would render quoted and HTSL would cast back to the lhs's type.
with NoTypeCasting():
    with Container() as container:
        a = PlayerStat('a').as_long()
        c = PlayerStat('c')
        c.value = f'{a}'
    htsl = container.into_htsl()

assert htsl == 'var "c" = %var.player/a 0% true', htsl


# NoTypeCasting + NoFallbackValues: the canonical bare form `%var.player/a%`,
# both for Stat rhs and for an equivalent Python-`str` rhs.
with NoTypeCasting(), NoFallbackValues():
    with Container() as container:
        a = PlayerStat('a').as_long()
        b = PlayerStat('b').as_long()
        b.value = a
        d = PlayerStat('d')
        d.value = f'{a}'
    htsl = container.into_htsl()

assert htsl == ('var "b" = %var.player/a% true\nvar "d" = %var.player/a% true'), htsl


# NoTypeCasting does not touch plain string literals — `housing_type_as_rhs`
# still wraps `'Alice'` in quotes, since stripping them would produce invalid
# HTSL.
with NoTypeCasting():
    with Container() as container:
        s = PlayerStat('s').as_string()
        s.value = 'Alice'
    htsl = container.into_htsl()

assert htsl == 'var "s" = "Alice" true', htsl


# NoTypeCasting in the simulator: a Python-`str` placeholder rhs goes through
# the native fullmatch path instead of the cast pipeline, so the lhs keeps
# the source type. With the flag off, `c` would store long 123.
with NoTypeCasting():
    with ExecutionContext() as ctx:
        a = PlayerStat('a').without_auto_unset()
        a.value = 123.0
        c = PlayerStat('c').without_auto_unset()
        c.value = f'{a}'

assert isinstance(ctx.get_raw(c), float), type(ctx.get_raw(c))
assert ctx.get_raw(c) == 123.0, ctx.get_raw(c)


# NoFallbackValues alone: typed-stat placeholders render without the
# fallback portion (` 0` / ` 0.0`); the L/D suffix and quotes are unaffected.
with NoFallbackValues():
    with Container() as container:
        a = PlayerStat('a').as_long()
        b = PlayerStat('b').as_long()
        b.value = a
    htsl = container.into_htsl()

assert htsl == 'var "b" = "%var.player/a%L" true', htsl


with NoFallbackValues():
    with Container() as container:
        a = PlayerStat('a').as_double()
        b = PlayerStat('b').as_double()
        b.value = a
    htsl = container.into_htsl()

assert htsl == 'var "b" = "%var.player/a%D" true', htsl


# NoOptimization: the peephole passes are skipped, so a redundant write
# survives instead of being eliminated as a dead store.
with NoOptimization():
    with Container() as container:
        x = PlayerStat('x').as_long()
        x.value = 5
        x.value = 10
    htsl = container.into_htsl()

assert htsl == 'var "x" = 5 true\nvar "x" = 10 true', htsl


# Sanity: without NoOptimization the same source collapses to a single write.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 5
    x.value = 10

assert container.into_htsl() == 'var "x" = 10 true', container.into_htsl()
