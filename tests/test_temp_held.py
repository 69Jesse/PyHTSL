"""A consumer-held `TemporaryStat` behaves like a normal scratch variable: it
keeps one stable `tmp<n>` name across every statement (and block) it appears in,
for both reads and writes, and never collides with consumer-named stats or the
optimizer's own per-statement temporaries."""

import io
import re
from contextlib import redirect_stdout

from pyhtsw import (
    Container,
    Else,
    ExecutionContext,
    GlobalStat,
    IfAll,
    PlayerStat,
    TemporaryStat,
    chat,
    create_function,
)

# --- A held temp written in if/else branches survives the read after the block.
# Regression: the optimizer used to merge the read away because the temp's
# branch writes were invisible to a forward temp-merge.
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_double()
    out = PlayerStat('out').as_double()
    t = TemporaryStat().as_double()
    ctx.put(x, -69.0, ignore_warning=True)
    with IfAll(x >= 0.0):
        t.value = x
    with Else:
        t.value = x + 360.0
    out.value = t + 90.0

    def check_branch(_o=out) -> None:
        assert abs(float(ctx.get_raw(_o)) - 381.0) < 1e-6, float(ctx.get_raw(_o))

    ctx.assert_all(check_branch)


# --- A held temp keeps one name across two separate functions. ---
with Container() as container:
    a = PlayerStat('a').as_long()
    t = TemporaryStat().as_long()

    @create_function('writer')
    def writer() -> None:
        t.value = a + 1

    @create_function('reader')
    def reader() -> None:
        chat(f'{t}')


htsl = container.into_htsl()
blocks = htsl.split('\n\n\n')
write_name = re.search(r'tmp\d+', next(b for b in blocks if 'a 0' in b)).group()
read_name = re.search(r'tmp\d+', next(b for b in blocks if 'chat' in b)).group()
assert write_name == read_name, (write_name, read_name, htsl)


# --- A held temp read in two f-strings reads the written value both times. ---
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        a = PlayerStat('a').as_long()
        t = TemporaryStat().as_long()
        ctx.put(a, 3, ignore_warning=True)
        t.value = a
        t.value *= 10
        chat(f'first {t}')
        chat(f'second {t}')
assert buf.getvalue().count('30') == 2, buf.getvalue()


# --- A held temp and a computed expression interpolate together cleanly. ---
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        t = TemporaryStat().as_long()
        ctx.put(x, 4, ignore_warning=True)
        t.value = 100
        chat(f'{t} and {x + 1}')
assert '100 and 5' in buf.getvalue(), buf.getvalue()


# --- Held temps work as operands of every flavour of op. ---
def _expect(build, expected: float) -> None:
    with ExecutionContext() as ctx:
        out = PlayerStat('out').as_long()
        build(out)

        def verify(_o=out, _e=expected) -> None:
            assert int(ctx.get_raw(_o)) == _e, (int(ctx.get_raw(_o)), _e)

        ctx.assert_all(verify)


def _self_mod(out) -> None:
    t = TemporaryStat().as_long()
    t.value = 17
    t.value = t.remainder(5)  # Java %
    out.value = t


def _abs(out) -> None:
    t = TemporaryStat().as_long()
    t.value = -42
    out.value = abs(t)


def _shift(out) -> None:
    t = TemporaryStat().as_long()
    t.value = 1
    t.value <<= 4
    out.value = t


_expect(_self_mod, 2)
_expect(_abs, 42)
_expect(_shift, 16)


# --- A typeless temp can be typed lazily, like any other stat. ---
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    scratch = TemporaryStat()  # no type yet
    ctx.put(x, 8, ignore_warning=True)
    scratch.as_long().value = x
    scratch.as_long().value += 2
    out = PlayerStat('out').as_long()
    out.value = scratch.as_long()

    def check_typeless(_o=out) -> None:
        assert int(ctx.get_raw(_o)) == 10, int(ctx.get_raw(_o))

    ctx.assert_all(check_typeless)


# --- A held string temp round-trips across statements. ---
with ExecutionContext() as ctx:
    s = TemporaryStat().as_string()
    s.value = 'ab'
    out = PlayerStat('out').as_string()
    out.value = s

    def check_string(_o=out) -> None:
        assert ctx.get_raw(_o) == 'ab', repr(ctx.get_raw(_o))

    ctx.assert_all(check_string)


# --- A held temp value flows into a GlobalStat. ---
with ExecutionContext() as ctx:
    g = GlobalStat('g').as_long()
    t = TemporaryStat().as_long()
    t.value = 7
    t.value += 5
    g.value = t

    def check_global(_g=g) -> None:
        assert int(ctx.get_raw(_g)) == 12, int(ctx.get_raw(_g))

    ctx.assert_all(check_global)


# --- Ten held temps stay distinct. ---
with ExecutionContext() as ctx:
    temps = [TemporaryStat().as_long() for _ in range(10)]
    for i, temp in enumerate(temps):
        temp.value = i * 100
    out = PlayerStat('out').as_long()
    out.value = temps[0] + temps[9]

    def check_ten(_o=out) -> None:
        assert int(ctx.get_raw(_o)) == 900, int(ctx.get_raw(_o))

    ctx.assert_all(check_ten)


# --- into_htsl is idempotent with a held temp (renders the same twice). ---
with Container() as container:
    a = PlayerStat('a').as_long()
    t = TemporaryStat().as_long()
    t.value = a + 1
    chat(f'{t}')

assert container.into_htsl() == container.into_htsl()


# --- Reservation is per-container: it does not leak into the next container. ---
with Container() as first:
    for i in range(6):
        PlayerStat(f'tmp{i}').as_long().value = i
first.into_htsl()

with Container() as second:
    a = PlayerStat('a').as_long()
    chat(f'{a + 1}')  # a surviving temp
nums = sorted({int(n) for n in re.findall(r'tmp(\d+)', second.into_htsl())})
assert nums == [0], second.into_htsl()
