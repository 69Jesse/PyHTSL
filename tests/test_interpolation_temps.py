"""Interpolating computed expressions into statement strings."""

import io
from contextlib import redirect_stdout

from pyhtsl import (
    Container,
    ExecutionContext,
    GlobalStat,
    HousePlayers,
    IfAll,
    PlayerStat,
    Random,
    chat,
    display_title,
)

# Two interpolations in one statement get distinct temps
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    chat(f'x={a + 1} y={b + 2}')

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'var "tmp1" = "%var.player/b 0%L" false\n'
    'var "tmp1" += 2 false\n'
    'chat "x=%var.player/tmp0 0% y=%var.player/tmp1 0%"'
), container.into_htsl()


# A single interpolation with its own sub-expressions
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    chat(f'{(a + 1) * (b + 2)}')

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'var "tmp1" = "%var.player/b 0%L" false\n'
    'var "tmp1" += 2 false\n'
    'var "tmp0" *= "%var.player/tmp1 0%L" false\n'
    'chat "%var.player/tmp0 0%"'
), container.into_htsl()


# A compound expression (modulo) interpolated
with Container() as container:
    a = PlayerStat('a').as_long()
    chat(f'{a % 5}')

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" /= 5 false\n'
    'var "tmp0" *= 5 false\n'
    'var "tmp1" = "%var.player/a 0%L" false\n'
    'var "tmp1" -= "%var.player/tmp0 0%L" false\n'
    'if and (var "tmp1" < 0 0) {\n'
    '    var "tmp1" += 5 false\n'
    '}\n'
    'chat "%var.player/tmp1 0%"'
), container.into_htsl()


# Temp numbers reset (reuse) across separate statements
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    chat(f'{a + 1}')
    chat(f'{b + 2}')

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'chat "%var.player/tmp0 0%"\n'
    'var "tmp0" = "%var.player/b 0%L" false\n'
    'var "tmp0" += 2 false\n'
    'chat "%var.player/tmp0 0%"'
), container.into_htsl()


# Interpolation across several string fields of one statement
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    display_title(f'T={a + 1}', f'S={b + 2}')

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'var "tmp1" = "%var.player/b 0%L" false\n'
    'var "tmp1" += 2 false\n'
    'title "T=%var.player/tmp0 0%" "S=%var.player/tmp1 0%" 1 5 1'
), container.into_htsl()


# The same expression object interpolated twice gets two temps
with Container() as container:
    a = PlayerStat('a').as_long()
    expr = a + 1
    chat(f'{expr} and {expr}')

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'var "tmp1" = "%var.player/a 0%L" false\n'
    'var "tmp1" += 1 false\n'
    'chat "%var.player/tmp0 0% and %var.player/tmp1 0%"'
), container.into_htsl()


# Interpolation inside a conditional resolves into the nested block
with Container() as container:
    a = PlayerStat('a').as_long()
    with IfAll(a > 0):
        chat(f'{a + 1}')

assert container.into_htsl() == (
    'if and (var "a" > 0 0) {\n'
    '    var "tmp0" = "%var.player/a 0%L" false\n'
    '    var "tmp0" += 1 false\n'
    '    chat "%var.player/tmp0 0%"\n'
    '}'
), container.into_htsl()


# The originally reported bug: averages dashboard
with Container() as container:
    n = GlobalStat('totalcounts').as_long()
    playersum = GlobalStat('totalplayersum').as_long()
    currentafk = GlobalStat('currentafk').as_long()
    afksum = GlobalStat('totalafksum').as_long()

    chat(f'&7Average Players:&e {playersum / n}')
    chat(
        f'&7AFK count:&e {currentafk}&7/&a{HousePlayers}&7 '
        f'(&b{(currentafk / HousePlayers) * 100}%&7)'
    )
    chat(f'&7Average AFK count:&e {afksum / n}&7 (&b{(afksum / playersum) * 100}%&7)')

assert container.into_htsl() == (
    'var "tmp0" = "%var.global/totalplayersum 0%L" false\n'
    'var "tmp0" /= "%var.global/totalcounts 0%L" false\n'
    'chat "&7Average Players:&e %var.player/tmp0 0%"\n'
    'var "tmp0" = "%var.global/currentafk 0%L" false\n'
    'var "tmp0" /= "%house.players%L" false\n'
    'var "tmp0" *= 100 false\n'
    'chat "&7AFK count:&e %var.global/currentafk 0%&7/&a%house.players%&7 '
    '(&b%var.player/tmp0 0%%&7)"\n'
    'var "tmp0" = "%var.global/totalafksum 0%L" false\n'
    'var "tmp0" /= "%var.global/totalcounts 0%L" false\n'
    'var "tmp1" = "%var.global/totalafksum 0%L" false\n'
    'var "tmp1" /= "%var.global/totalplayersum 0%L" false\n'
    'var "tmp1" *= 100 false\n'
    'chat "&7Average AFK count:&e %var.player/tmp0 0%&7 (&b%var.player/tmp1 0%%&7)"'
), container.into_htsl()


# Execution: two interpolations compute independent, correct values
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        a = PlayerStat('a').as_long()
        b = PlayerStat('b').as_long()
        ctx.put(a, 10)
        ctx.put(b, 20)
        chat(f'A={a + 1} B={b + 2}')

output = buf.getvalue()
assert 'A=11 B=22' in output, output


# Execution: a nested interpolation computes the right value
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        a = PlayerStat('a').as_long()
        b = PlayerStat('b').as_long()
        ctx.put(a, 10)
        ctx.put(b, 20)
        chat(f'N={(a + 1) * (b + 2)}')

output = buf.getvalue()
assert 'N=242' in output, output


# Execution: a modulo interpolation computes the right value
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        a = PlayerStat('a').as_long()
        ctx.put(a, 13)
        chat(f'M={a % 5}')

output = buf.getvalue()
assert 'M=3' in output, output


# Execution: temps reused across statements stay correct
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        a = PlayerStat('a').as_long()
        b = PlayerStat('b').as_long()
        ctx.put(a, 10)
        ctx.put(b, 20)
        chat(f'first={a + 1}')
        chat(f'second={b + 2}')

output = buf.getvalue()
assert 'first=11' in output, output
assert 'second=22' in output, output
