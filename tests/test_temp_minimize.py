"""Temp `tmp<n>` names are scarce (we deliberately overwrite old stats), so each
function must pack its temps into the fewest numbers: numbering resets per
function (no accumulation across the program) and reuses a number as soon as the
temp holding it is past its last use (interval colouring)."""

import re

from pyhtsw import (
    Container,
    ExecutionContext,
    PlayerStat,
    TemporaryStat,
    chat,
    create_function,
)


def max_temp(htsl: str) -> int:
    nums = [int(n) for n in re.findall(r'\btmp(\d+)\b', htsl)]
    return max(nums) if nums else -1


def block_htsl(container: Container, name: str) -> str:
    block = next(b for b in container.blocks if b.get_name() == name)
    return block.into_htsl()


# --- Numbering resets per function (no cross-function accumulation). ---
with Container() as container:

    @create_function('Alpha')
    def alpha() -> None:
        t = TemporaryStat().as_long()
        t.value = 10
        t.value += 5
        chat(f'{t}')

    @create_function('Beta')
    def beta() -> None:
        u = TemporaryStat().as_long()
        u.value = 20
        u.value += 5
        chat(f'{u}')


# Each function starts at tmp0 — Beta does not continue from Alpha's numbers.
assert max_temp(block_htsl(container, 'Alpha')) == 0, block_htsl(container, 'Alpha')
assert max_temp(block_htsl(container, 'Beta')) == 0, block_htsl(container, 'Beta')


# --- Non-overlapping held temps reuse the same number (interval colouring). ---
with Container() as container:

    @create_function('Sequential')
    def sequential() -> None:
        a = PlayerStat('a').as_long()
        out = PlayerStat('out').as_long()
        # Three held temps, each used and finished before the next begins.
        t1 = TemporaryStat().as_long()
        t1.value = a
        t1.value += 1
        out.value = t1
        t2 = TemporaryStat().as_long()
        t2.value = a
        t2.value += 2
        out.value += t2
        t3 = TemporaryStat().as_long()
        t3.value = a
        t3.value += 3
        out.value += t3


# All three reuse tmp0 (none overlap), plus at most a transient.
htsl = block_htsl(container, 'Sequential')
assert max_temp(htsl) <= 1, htsl


# --- Overlapping held temps stay distinct (correctness over packing). ---
with ExecutionContext() as ctx:
    a = PlayerStat('a').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(a, 100, ignore_warning=True)
    t1 = TemporaryStat().as_long()
    t2 = TemporaryStat().as_long()
    t1.value = a  # both live at once
    t2.value = a
    t2.value += 1
    out.value = t1 + t2  # 100 + 101

    def check_overlap(_o=out) -> None:
        assert int(ctx.get_raw(_o)) == 201, int(ctx.get_raw(_o))

    ctx.assert_all(check_overlap)


# --- Reuse is correct, not just compact: a reused number computes right. ---
with ExecutionContext() as ctx:
    a = PlayerStat('a').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(a, 5, ignore_warning=True)
    ctx.put(out, 0, ignore_warning=True)
    for i in range(1, 4):
        t = TemporaryStat().as_long()  # fresh temp each round, reuses the number
        t.value = a
        t.value *= i
        out.value += t  # 5*1 + 5*2 + 5*3 = 30

    def check_reuse(_o=out) -> None:
        assert int(ctx.get_raw(_o)) == 30, int(ctx.get_raw(_o))

    ctx.assert_all(check_reuse)
