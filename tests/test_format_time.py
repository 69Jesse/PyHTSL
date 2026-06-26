"""format_time_string renders durations; set_ordinal_inline gives ordinal suffixes."""

from pyhtsw import ExecutionContext, PlayerStat
from pyhtsw.ext import format_time_string, set_ordinal_inline


def check_time(seconds: int, separator: str, expected: str) -> None:
    with ExecutionContext() as ctx:
        out = PlayerStat('out').as_string()
        format_time_string(seconds, output=out, separator=separator)

        def verify(_o=out, _e=expected, _s=seconds, _sep=separator) -> None:
            got = ctx.get_raw(_o)
            assert got == _e, (_s, repr(_sep), 'got', repr(got), 'want', repr(_e))

        ctx.assert_all(verify)


# No separator
check_time(0, '', '0s')
check_time(5, '', '5s')
check_time(65, '', '1m5s')
check_time(3661, '', '1h1m1s')
check_time(90061, '', '1d1h1m')  # seconds dropped once days appear

# Many days — the days unit must keep counting, not roll into hours
check_time(604800, '', '7d0h0m')  # exactly one week
check_time(2243760, '', '25d23h16m')  # 25d23h16m (the regression-report value)
check_time(1000000, '', '11d13h46m')

# With a space separator (between unit groups only)
check_time(0, ' ', '0s')
check_time(5, ' ', '5s')
check_time(65, ' ', '1m 5s')
check_time(3661, ' ', '1h 1m 1s')
check_time(90061, ' ', '1d 1h 1m')
check_time(2243760, ' ', '25d 23h 16m')

# Negative clamps to zero
check_time(-100, ' ', '0s')


# A computed input (the real-world call shape) works, and a consumer stat the
# helper's managed temps could once have clobbered survives untouched.
def check_computed() -> None:
    with ExecutionContext() as ctx:
        ending_at = PlayerStat('ENDING_AT').as_long()
        now = PlayerStat('DateUnix').as_long()
        tmp0 = PlayerStat('tmp0').as_long()  # consumer's own tmp0
        out = PlayerStat('out').as_string()
        ctx.put(ending_at, 2243760, ignore_warning=True)
        ctx.put(now, 0, ignore_warning=True)
        tmp0.value = 777
        format_time_string(abs(ending_at - now), output=out)

        def verify(_o=out, _t=tmp0) -> None:
            assert ctx.get_raw(_o) == '25d23h16m', repr(ctx.get_raw(_o))
            assert int(ctx.get_raw(_t)) == 777, ctx.get_raw(_t)

        ctx.assert_all(verify)


check_computed()


def check_ordinal(n: int, expected: str) -> None:
    with ExecutionContext() as ctx:
        value = PlayerStat('n').as_long()
        ctx.put(value, n, ignore_warning=True)
        out = PlayerStat('suffix').as_string()
        set_ordinal_inline(value, out)

        def verify(_o=out, _e=expected, _n=n) -> None:
            got = ctx.get_raw(_o)
            assert got == _e, (_n, 'got', repr(got), 'want', repr(_e))

        ctx.assert_all(verify)


for number, suffix in (
    (1, 'st'),
    (2, 'nd'),
    (3, 'rd'),
    (4, 'th'),
    (10, 'th'),
    (11, 'th'),
    (12, 'th'),
    (13, 'th'),
    (21, 'st'),
    (22, 'nd'),
    (23, 'rd'),
    (111, 'th'),
    (101, 'st'),
):
    check_ordinal(number, suffix)
