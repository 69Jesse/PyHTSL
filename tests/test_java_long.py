"""Java `long` semantics: the `pyhtsl.execute.java_long` primitives plus the
executor and constant folder built on them.

A Hypixel housing long is a JVM `long` — a 64-bit two's-complement integer — so
arithmetic wraps on overflow, division truncates toward zero, modulo takes the
sign of the dividend, and shift counts are masked to their low 6 bits.
"""

from pyhtsl import Container, ExecutionContext, PlayerStat
from pyhtsl.execute import java_long
from pyhtsl.execute.java_long import INT64_MAX, INT64_MIN, JavaLong

# === JavaLong construction wraps into the signed 64-bit range ===
assert int(JavaLong(INT64_MAX)) == INT64_MAX
assert int(JavaLong(INT64_MAX + 1)) == INT64_MIN
assert int(JavaLong(INT64_MIN - 1)) == INT64_MAX
assert int(JavaLong(2**64)) == 0
assert int(JavaLong(-(2**63))) == INT64_MIN
assert isinstance(JavaLong(5), int)  # stays int-compatible for the rest of pyhtsl


# === Addition / subtraction / multiplication wrap on overflow ===
assert java_long.add(2, 3) == 5
assert java_long.add(INT64_MAX, 1) == INT64_MIN
assert java_long.sub(INT64_MIN, 1) == INT64_MAX
assert java_long.mul(INT64_MAX, 2) == -2  # Java: 9223372036854775807 * 2
assert java_long.mul(INT64_MIN, -1) == INT64_MIN  # negating MIN overflows to MIN
assert java_long.neg(INT64_MIN) == INT64_MIN


# === Integer division truncates toward zero (Python // floors) ===
assert java_long.div(7, 2) == 3
assert java_long.div(-7, 2) == -3  # a floor division would give -4
assert java_long.div(7, -2) == -3
assert java_long.div(-7, -2) == 3
assert java_long.div(INT64_MIN, -1) == INT64_MIN  # overflow wraps


# === Modulo takes the sign of the dividend ===
assert java_long.mod(7, 3) == 1
assert java_long.mod(-7, 3) == -1  # Python % would give 2
assert java_long.mod(7, -3) == 1  # Python % would give -2
assert java_long.mod(-7, -3) == -1
assert java_long.mod(INT64_MIN, -1) == 0


# === Shift counts are masked to their low 6 bits ===
assert java_long.shl(1, 3) == 8
assert java_long.shl(1, 63) == INT64_MIN
assert java_long.shl(1, 64) == 1  # 64 & 63 == 0, no shift
assert java_long.shl(1, 65) == 2  # 65 & 63 == 1
assert java_long.shr(1024, 2) == 256
assert java_long.shr(-8, 1) == -4  # arithmetic shift: the sign bit propagates
assert java_long.shr(-8, 64) == -8  # 64 & 63 == 0


# === Logical right shift zero-fills, masks the count, and never crashes ===
assert java_long.ushr(16, 2) == 4
assert java_long.ushr(-1, 1) == INT64_MAX  # 0xFFFF...FFFF >>> 1
assert java_long.ushr(-8, 1) == (2**63) - 4  # 9223372036854775804
assert java_long.ushr(-1, 0) == -1  # >>> 0 is the identity
assert java_long.ushr(-1, 64) == -1  # 64 & 63 == 0
assert java_long.ushr(-1, -1) == 1  # -1 & 63 == 63 — masked, not a ValueError


# === Bitwise operators on the two's-complement bit pattern ===
assert java_long.bit_and(-8, 0xF) == 8
assert java_long.bit_or(-8, 7) == -1
assert java_long.bit_xor(-1, -1) == 0


# === Java's `(long) double` narrowing cast ===
assert java_long.from_double(2.7) == 2  # truncates toward zero
assert java_long.from_double(-2.7) == -2  # toward zero, not -3
assert java_long.from_double(float('nan')) == 0
assert java_long.from_double(float('inf')) == INT64_MAX
assert java_long.from_double(float('-inf')) == INT64_MIN
assert java_long.from_double(1e308) == INT64_MAX  # beyond long range -> clamp


# === The executor wraps long arithmetic exactly like a JVM ===
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, INT64_MAX, ignore_warning=True)
    x.value += 1

assert int(ctx.get_raw(x)) == INT64_MIN, ctx.get_raw(x)


# Integer division through the executor truncates toward zero.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, -7, ignore_warning=True)
    x.value //= 2

assert int(ctx.get_raw(x)) == -3, ctx.get_raw(x)


# A shift count past 63 is masked, not undefined behaviour.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, 1, ignore_warning=True)
    x.value <<= 65  # 65 & 63 == 1

assert int(ctx.get_raw(x)) == 2, ctx.get_raw(x)


# Logical right shift of a negative long zero-fills and never raises.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    ctx.put(x, -1, ignore_warning=True)
    x.logical_rshift(1).write()

assert int(ctx.get_raw(x)) == INT64_MAX, ctx.get_raw(x)


# The `remainder` primitive composes to Java's `%`: a truncated quotient
# leaves a remainder with the sign of the dividend.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(x, -7, ignore_warning=True)
    out.value = x.remainder(3)

assert int(ctx.get_raw(out)) == -1, ctx.get_raw(out)


# PyHTSL's `%` operator stays Python-flavoured on purpose — it adjusts the
# truncated remainder so the result instead takes the sign of the divisor.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(x, -7, ignore_warning=True)
    out.value = x % 3

assert int(ctx.get_raw(out)) == 2, ctx.get_raw(out)


# === The constant folder wraps long results exactly like the executor ===
# `x = MAX; x += 1` folds to a single Set of the wrapped value.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = INT64_MAX
    x.value += 1

assert container.into_htsl() == f'var "x" = {INT64_MIN} true', container.into_htsl()


# Small consecutive shifts still fold: 20 + 20 == 40 stays under the 6-bit mask.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value <<= 20
    x.value <<= 20

assert container.into_htsl() == 'var "x" <<= 40 true', container.into_htsl()


# ...but a fold is declined when the mask would change the result: two `<< 40`
# are not `<< 80` (80 & 63 == 16), so both shifts must survive.
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value <<= 40
    x.value <<= 40

assert container.into_htsl() == 'var "x" <<= 40 true\nvar "x" <<= 40 true', (
    container.into_htsl()
)
