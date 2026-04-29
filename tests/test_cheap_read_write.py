"""cheap_read / cheap_write across widths and lengths.

Verifies the correct slot is read from / written to for several (width, length)
pairs that exercise both special-case branches (len <= 4) and the recursive
chunked branch (len > 4 for reads, len > 25 for writes).
"""

import random

from helpers import expect_exception

from pyhtsl import ExecutionContext, PlayerStat
from pyhtsl.ext.cheap_read_write import cheap_read, cheap_write


def sample_targets(length: int) -> list[int]:
    return random.sample(range(length), min(20, length))


def value_at(i: int, k: int) -> int:
    return i * 1000 + k + 1  # nonzero so a read into a default-0 stat is detectable


# --- cheap_read: reads return the targeted item ---

for length in (1, 10, 100):
    for width in (1, 3):
        with ExecutionContext(ignore_action_limits=True) as ctx:
            sources = [
                tuple(PlayerStat(f'src{i}_{k}').as_long() for k in range(width))
                for i in range(length)
            ]
            for i in range(length):
                for k in range(width):
                    ctx.put(sources[i][k], value_at(i, k))

            items_arg = [s[0] for s in sources] if width == 1 else list(sources)

            index = PlayerStat('idx').as_long()
            outputs = tuple(PlayerStat(f'o{k}').as_long() for k in range(width))
            output_arg = outputs[0] if width == 1 else outputs

            for target in sample_targets(length):
                index.value = target
                cheap_read(items=items_arg, index=index, output=output_arg)

                def check_read(
                    _w: int = width,
                    _len: int = length,
                    _t: int = target,
                    _outs: tuple[PlayerStat, ...] = outputs,
                ) -> None:
                    for k in range(_w):
                        got = int(ctx.get(_outs[k]))
                        want = value_at(_t, k)
                        assert got == want, (
                            f'read width={_w} length={_len} target={_t}: '
                            f'output[{k}]={got}, want {want}'
                        )

                ctx.assert_all(check_read)


# --- cheap_write: only the targeted slot changes; others keep their prior value ---

NEW_OFFSET = 1_000_000  # added to value_at to make the post-write value distinct


for length in (1, 10, 100):
    for width in (1, 3):
        with ExecutionContext(ignore_action_limits=True) as ctx:
            slots = [
                tuple(PlayerStat(f's{i}_{k}').as_long() for k in range(width))
                for i in range(length)
            ]
            for i in range(length):
                for k in range(width):
                    ctx.put(slots[i][k], value_at(i, k))

            index = PlayerStat('idx').as_long()
            items_arg = [s[0] for s in slots] if width == 1 else list(slots)
            promoted: set[int] = set()

            for target in sample_targets(length):
                promoted.add(target)
                index.value = target
                new_inputs = tuple(
                    value_at(target, k) + NEW_OFFSET for k in range(width)
                )
                input_arg = new_inputs[0] if width == 1 else new_inputs

                cheap_write(items=items_arg, index=index, input=input_arg)

                def check_write(
                    _w: int = width,
                    _len: int = length,
                    _t: int = target,
                    _slots: list[tuple[PlayerStat, ...]] = slots,
                    _promoted: frozenset[int] = frozenset(promoted),
                ) -> None:
                    for i in range(_len):
                        for k in range(_w):
                            got = int(ctx.get(_slots[i][k]))
                            want = value_at(i, k) + (
                                NEW_OFFSET if i in _promoted else 0
                            )
                            assert got == want, (
                                f'write width={_w} length={_len} target={_t}: '
                                f'item[{i}][{k}]={got}, want {want}'
                            )

                ctx.assert_all(check_write)


# --- failure cases for cheap_read ---

# Empty items list
with expect_exception(ValueError):
    cheap_read(
        items=[],
        index=PlayerStat('idx').as_long(),
        output=PlayerStat('out').as_long(),
    )

# Mismatched widths within items
with expect_exception(ValueError):
    cheap_read(
        items=[(1, 2), (3, 4, 5)],
        index=PlayerStat('idx').as_long(),
        output=(PlayerStat('a').as_long(), PlayerStat('b').as_long()),
    )

# Output width doesn't match items width
with expect_exception(ValueError):
    cheap_read(
        items=[(1, 2), (3, 4)],
        index=PlayerStat('idx').as_long(),
        output=PlayerStat('a').as_long(),
    )

# Width exceeds the supported maximum (12)
big = tuple(range(13))
with expect_exception(ValueError):
    cheap_read(
        items=[big, big],
        index=PlayerStat('idx').as_long(),
        output=tuple(PlayerStat(f'o{k}').as_long() for k in range(13)),
    )
