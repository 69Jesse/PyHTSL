"""Action limits count rendered HTSL actions, not expression objects.

A single `BinaryExpression` can flatten into several `var` lines (temps, etc.),
so a block with 25 objects can still emit 26 "change variable" actions. The
limit fixer must count what is rendered and split the overflow (HTSL caps each
function at 25 stat changes), not trust the object count.
"""

from pyhtsw import (
    Container,
    PlayerStat,
    create_function,
)


def _top_level_and_total_var_lines(block_htsl: str) -> tuple[int, int]:
    """(var lines at brace-depth 0, total var lines) for one block's HTSL."""
    depth = 0
    top_level = 0
    total = 0
    for line in block_htsl.split('\n'):
        stripped = line.strip()
        if stripped.startswith('var '):
            total += 1
            if depth == 0:
                top_level += 1
        depth += stripped.count('{') - stripped.count('}')
    return top_level, total


# 24 single-action writes + 1 two-action assignment = 25 objects but 26 actions.
# Object counting would think this fits; action counting must split it.
with Container() as container:
    stats = [PlayerStat(f's{i}').as_long() for i in range(30)]

    @create_function('limit overflow')
    def limit_overflow() -> None:
        for i in range(24):
            stats[i].value = i + 1
        stats[24].value = stats[25] + stats[26]  # renders to 2 var lines


htsl = next(
    block.into_htsl()
    for block in container.blocks
    if block.get_name() == 'limit overflow'
)

top_level, total = _top_level_and_total_var_lines(htsl)
# The overflow gets wrapped into an always-true `if and () { ... }` (a whole
# expression at a time), so the top level stays within the 25 cap while all 26
# actions are still emitted.
assert top_level <= 25, (top_level, htsl)
assert total == 26, (total, htsl)
assert 'if and () {' in htsl, htsl


# Control: exactly 25 actions (25 single-action writes) needs no splitting.
with Container() as container:
    stats = [PlayerStat(f'c{i}').as_long() for i in range(25)]

    @create_function('at limit')
    def at_limit() -> None:
        for i in range(25):
            stats[i].value = i + 1


htsl = next(
    block.into_htsl() for block in container.blocks if block.get_name() == 'at limit'
)
top_level, total = _top_level_and_total_var_lines(htsl)
assert top_level == 25 and total == 25, (top_level, total, htsl)
assert 'if and () {' not in htsl, htsl


# A single expression that on its own renders to more actions than the cap
# (`a = b0 + b1 + ... + b25` -> 26 var lines) can be neither wrapped nor moved.
# It must be emitted as-is, and must not send the splitter into an infinite loop
# of overflow blocks.
with Container() as container:
    bs = [PlayerStat(f'b{i}').as_long() for i in range(26)]
    a = PlayerStat('a').as_long()

    @create_function('single big')
    def single_big() -> None:
        total = bs[0]
        for i in range(1, 26):
            total = total + bs[i]
        a.value = total


htsl = next(
    block.into_htsl() for block in container.blocks if block.get_name() == 'single big'
)
_, total = _top_level_and_total_var_lines(htsl)
assert total == 26, (total, htsl)
assert 'if and () {' not in htsl, htsl
