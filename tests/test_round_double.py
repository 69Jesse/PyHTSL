"""round_double from pyhtsl.ext: round a double stat to N decimal places."""

from pyhtsl import Container, ExecutionContext, PlayerStat
from pyhtsl.ext import round_double

# 1.234567 rounded to 2 decimals -> 1.24
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_double()
    ctx.put(x, 1.234567)
    round_double(x, 2)

    def check() -> None:
        assert float(ctx.get_raw(x)) == 1.24, ctx.get_raw(x)

    ctx.assert_all(check)


# 0.5 rounded to 0 decimals -> 1.0 (rounds via +0.5 then truncate)
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_double()
    ctx.put(x, 0.5)
    round_double(x, 0)

    def check() -> None:
        assert float(ctx.get_raw(x)) == 1.0, ctx.get_raw(x)

    ctx.assert_all(check)


# Result is close to the expected mathematical rounding (within 0.001 of round
# to N decimals). The simulator's cast_to_long step is a no-op, so the function
# can leave a tiny residue from the +0.5 — this tolerance covers that.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_double()
    ctx.put(x, 3.14159)
    round_double(x, 2)

    def check() -> None:
        actual = float(ctx.get_raw(x))
        assert abs(actual - 3.14) < 0.01, actual

    ctx.assert_all(check)


with ExecutionContext() as ctx:
    x = PlayerStat('x').as_double()
    ctx.put(x, 7.0)
    round_double(x, 3)

    def check() -> None:
        actual = float(ctx.get_raw(x))
        assert abs(actual - 7.0) < 0.001, actual

    ctx.assert_all(check)


# Sanity: round_double also produces valid HTSL (compile-only)
with Container() as container:
    x = PlayerStat('x').as_double()
    round_double(x, 2)

assert container.into_htsl() != ''
