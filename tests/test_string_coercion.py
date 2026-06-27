"""Housing coerces a set-string value that reads as a number — including a
numeric value with a trailing `L`/`D` suffix, matched case-insensitively (a
long/double literal) — into a number, not a string. The executor models this so
it reproduces the in-game behaviour. It is exactly why "6d" rendered as "6"
(turning "6d7h7m" into "67h7m"), and why format_time_string must never build a
bare "<number>d"."""

from pyhtsw import ExecutionContext, PlayerStat


def append_x(suffix: str, value: int) -> str:
    """Set a string to "<value><suffix>", then append 'x' and return the result.
    If the suffix coerced the value to a number it is swallowed, so 'x' lands
    right after the number."""
    captured: dict[str, object] = {}
    with ExecutionContext() as ctx:
        n = PlayerStat('n').as_long()
        s = PlayerStat('s').as_string()
        out = PlayerStat('out').as_string()
        ctx.put(n, value, ignore_warning=True)
        s.value = f'{n}{suffix}'
        out.value = f'{s}x'

        def grab(_o=out) -> None:
            captured['v'] = ctx.get_raw(_o)

        ctx.run(grab)
    return str(captured['v'])


# d / l (any case) read as double/long literal suffixes -> swallowed.
assert append_x('d', 6) == '6x', append_x('d', 6)
assert append_x('D', 6) == '6x', append_x('D', 6)
assert append_x('l', 42) == '42x', append_x('l', 42)
assert append_x('L', 42) == '42x', append_x('L', 42)

# h / m / s are not literal suffixes -> the value stays a string, suffix kept.
assert append_x('h', 6) == '6hx', append_x('h', 6)
assert append_x('m', 7) == '7mx', append_x('m', 7)
assert append_x('s', 9) == '9sx', append_x('s', 9)


# A non-numeric base is never coerced, even ending in 'd'.
with ExecutionContext() as ctx:
    out = PlayerStat('out').as_string()
    out.value = 'load'

    def keep_string(_o=out) -> None:
        assert ctx.get_raw(_o) == 'load', ctx.get_raw(_o)

    ctx.assert_all(keep_string)
