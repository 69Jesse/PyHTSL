"""Tests for the chunking helpers in `pyhtsl.helpers`.

`chunked(IfAll(...))` spreads a body that overflows HTSL's per-block action
cap across several sequential `if` blocks; `chunked(Else)` then packs a large
`else` body into those blocks' empty `else` slots, appending extra empty-`if`
blocks only once the slots run out.

A flat write of distinct stats survives the optimizer untouched, so a body of
N such writes is exactly `ceil(N / 25)` chunks (25 = the per-block stat-change
cap).
"""

import io
from contextlib import redirect_stdout

from helpers import expect_exception

from pyhtsl import (
    Container,
    Else,
    ExecutionContext,
    IfAll,
    IfAny,
    PlayerStat,
    chunked,
)

# === Execution: the right branch runs ===

# Condition true -> every `if` chunk runs, no `else` chunk does.
with ExecutionContext(ignore_action_limits=True) as ctx:
    cond = PlayerStat('cond').as_long()
    ctx.put(cond, 1, ignore_warning=True)
    result = PlayerStat('result').as_long()
    fillers = [PlayerStat(f'f{i}').as_long() for i in range(40)]
    with chunked(IfAll(cond > 0)):
        for f in fillers:
            f.value = 7
        result.value = 111
    with chunked(Else):
        for f in fillers:
            f.value = 9
        result.value = 222

    def check_if_branch() -> None:
        assert int(ctx.get(result)) == 111
        assert int(ctx.get(fillers[0])) == 7
        assert int(ctx.get(fillers[39])) == 7

    ctx.assert_all(check_if_branch)


# Condition false -> every `else` chunk runs, no `if` chunk does.
with ExecutionContext(ignore_action_limits=True) as ctx:
    cond = PlayerStat('cond').as_long()
    ctx.put(cond, 0, ignore_warning=True)
    result = PlayerStat('result').as_long()
    fillers = [PlayerStat(f'f{i}').as_long() for i in range(40)]
    with chunked(IfAll(cond > 0)):
        for f in fillers:
            f.value = 7
        result.value = 111
    with chunked(Else):
        for f in fillers:
            f.value = 9
        result.value = 222

    def check_else_branch() -> None:
        assert int(ctx.get(result)) == 222
        assert int(ctx.get(fillers[0])) == 9
        assert int(ctx.get(fillers[39])) == 9

    ctx.assert_all(check_else_branch)


# A tiny `if` next to a large `else`: the else overflows the one `if` block's
# slot, so the extra empty-`if` blocks must still run their `else` on a false
# condition.
with ExecutionContext(ignore_action_limits=True) as ctx:
    cond = PlayerStat('cond').as_long()
    ctx.put(cond, 0, ignore_warning=True)
    outs = [PlayerStat(f'o{i}').as_long() for i in range(60)]
    with chunked(IfAll(cond > 0)):
        PlayerStat('tiny').as_long().value = 1
    with chunked(Else):
        for i, o in enumerate(outs):
            o.value = i + 1

    def check_extra_else_blocks(_outs: list = outs) -> None:
        for i in range(60):
            got = int(ctx.get(_outs[i]))
            assert got == i + 1, f'extra-else out {i}: got {got}, want {i + 1}'

    ctx.assert_all(check_extra_else_blocks)


# `IfAny` works as a template just like `IfAll`.
with ExecutionContext(ignore_action_limits=True) as ctx:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    ctx.put(a, 0, ignore_warning=True)
    ctx.put(b, 5, ignore_warning=True)
    result = PlayerStat('result').as_long()
    fillers = [PlayerStat(f'f{i}').as_long() for i in range(40)]
    with chunked(IfAny(a > 0, b > 0)):
        for f in fillers:
            f.value = 1
        result.value = 1
    with chunked(Else):
        for f in fillers:
            f.value = 2
        result.value = 2

    def check_ifany() -> None:
        assert int(ctx.get(result)) == 1  # b > 0 satisfies IfAny

    ctx.assert_all(check_ifany)


# === Rendered structure ===
#
# 25 is the per-block stat-change cap, so N distinct writes -> ceil(N / 25)
# chunks. `chunked(Else)` fills existing blocks' `else` slots before it makes
# new ones.


def _render(n_if: int, n_else: int) -> str:
    with Container() as container:
        cond = PlayerStat('rc').as_long()
        with chunked(IfAll(cond > 0)):
            for i in range(n_if):
                PlayerStat(f'ri{i}').as_long().value = i + 1
        with chunked(Else):
            for i in range(n_else):
                PlayerStat(f're{i}').as_long().value = i + 1
    return container.into_htsl()


def _counts(htsl: str) -> tuple[int, int]:
    return htsl.count('if and'), htsl.count('} else {')


# Both small: a single `if / else`.
assert _counts(_render(3, 3)) == (1, 1)

# Big `if` (3 chunks), small `else` (1 chunk): the else drops into the first
# block's slot, no extra blocks.
assert _counts(_render(60, 3)) == (3, 1)

# Small `if` (1 chunk), big `else` (3 chunks): one slot filled, two extra
# empty-`if` blocks appended.
assert _counts(_render(3, 60)) == (3, 3)

# Big `if` (3 chunks), big `else` with fewer chunks (2): both else chunks land
# in existing slots, no extra blocks.
assert _counts(_render(60, 40)) == (3, 2)

# Big `if` (2 chunks), bigger `else` (4 chunks): two slots filled, two extra
# blocks appended.
assert _counts(_render(40, 80)) == (4, 4)

# Equal big bodies: every block gets exactly one else chunk, no extras.
assert _counts(_render(60, 60)) == (3, 3)


# The extra blocks carry an empty `if` body.
_extra_htsl = _render(3, 60)
assert _extra_htsl.count('if and') == 3
# Two of the three blocks have nothing before their `else`.
assert _extra_htsl.count('0) {\n} else {') == 2


# === Finalization through a real Container respects the action limits ===
#
# ExecutionContext ignores the limits; a plain Container enforces them, so
# this is what proves each chunk (if-side and else-side) stays legal.
with redirect_stdout(io.StringIO()):
    with Container() as container:
        cond = PlayerStat('fc').as_long()
        with chunked(IfAll(cond > 0)):
            for i in range(60):
                PlayerStat(f'fa{i}').as_long().value = i + 1
        with chunked(Else):
            for i in range(60):
                PlayerStat(f'fb{i}').as_long().value = i + 1
    assert container.into_htsl()


# === Failure cases ===

# `chunked(Else)` with no chunked `if` (or plain `if`) in front of it.
with expect_exception(SyntaxError):
    with Container():
        with chunked(Else):
            PlayerStat('x').as_long().value = 1

# A nested if/random block inside a `chunked(IfAll(...))` body cannot be split.
with expect_exception(SyntaxError):
    with Container():
        cond = PlayerStat('c').as_long()
        with chunked(IfAll(cond > 0)):
            with IfAll(cond > 0):
                PlayerStat('x').as_long().value = 1

# Same guard for a `chunked(Else)` body.
with expect_exception(SyntaxError):
    with Container():
        cond = PlayerStat('c').as_long()
        with chunked(IfAll(cond > 0)):
            PlayerStat('x').as_long().value = 1
        with chunked(Else):
            with IfAll(cond > 0):
                PlayerStat('y').as_long().value = 1
