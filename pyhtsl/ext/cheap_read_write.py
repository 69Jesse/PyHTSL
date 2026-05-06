import math
from collections.abc import Iterable, Sequence
from typing import Any

from ..actions.conditional.statements import Else, IfAll, IfAny
from ..editable import Checkable, Editable, HousingType
from ..internal_type import InternalType
from ..stats.player_stat import PlayerStat

__all__ = (
    'cheap_read',
    'cheap_write',
)


def assign(
    dst: Sequence[Editable],
    src: Sequence[Checkable | HousingType],
) -> None:
    for d, s in zip(dst, src, strict=True):
        d.value = s


def make_temps(
    i: int,
    template: Sequence[Checkable | HousingType],
) -> tuple[PlayerStat, ...]:
    width = len(template)
    return tuple(
        PlayerStat(f'tmp{i * width + k}').as_type(InternalType.from_value(template[k]))
        for k in range(width)
    )


def cheap_read_inner(
    *,
    items: Sequence[Sequence[Checkable | HousingType]],
    index: Editable,
    output: Sequence[Editable],
) -> None:
    width = len(items[0])
    is_start = True

    while len(items) > 4:
        part_size = min(24 // width, (len(items) + 1) // 2)
        new_items: list[tuple[Editable, ...]] = [
            make_temps(i, items[0]) for i in range(part_size)
        ]

        chunk_starts = list(range(part_size, len(items), part_size))
        for idx, chunk_start in enumerate(chunk_starts):
            chunk_end = min(chunk_start + part_size, len(items))
            with IfAll(index >= chunk_start, index < chunk_end):
                index.value -= chunk_start
                for i, j in enumerate(range(chunk_start, chunk_end)):
                    assign(new_items[i], items[j])
            if is_start and idx == 0:
                with Else:
                    for i in range(part_size):
                        assign(new_items[i], items[i])

        is_start = False
        items = new_items

    if len(items) == 1:
        assign(output, items[0])
    elif len(items) == 2:
        with IfAll(index == 0):
            assign(output, items[0])
        with Else:
            assign(output, items[1])
    elif len(items) == 3:
        with IfAll(index < 2):
            assign(output, items[1])
        with Else:
            assign(output, items[2])
        with IfAll(index == 0):
            assign(output, items[0])
    else:  # len(items) == 4
        temp_stat = make_temps(0, items[0])
        with IfAll(index < 2):
            assign(temp_stat, items[0])
            assign(output, items[1])
        with Else:
            assign(temp_stat, items[2])
            assign(output, items[3])
        with IfAny(index == 0, index == 2):
            assign(output, temp_stat)


def cheap_write_inner(
    *,
    items: Sequence[Sequence[Editable]],
    index: Editable,
    input: Sequence[Checkable | HousingType],
) -> None:
    width = len(items[0])
    n = len(items)

    if n == 1:
        assign(items[0], input)
        return

    best_ce = n
    best_be = 0
    best_cs = 0
    best_hoist = False
    for hoist in (False, True):
        max_cs = (25 if hoist else 23) // width
        be = 2 if hoist else 0
        for cs in range(1, min(max_cs, n - 1) + 1):
            ce = 2 * math.ceil(n / cs) - 1 + cs
            if (ce, be) < (best_ce, best_be):
                best_ce, best_be, best_cs, best_hoist = ce, be, cs, hoist

    if best_cs == 0:
        for i, item in enumerate(items):
            with IfAll(index == i):
                assign(item, input)
        return

    chunk_size = best_cs
    hoist = best_hoist
    temp_stats: list[tuple[Editable, ...]] = [
        make_temps(j, items[0]) for j in range(chunk_size)
    ]
    chunk_idx_stat = PlayerStat(f'tmp{chunk_size * width}').as_long()

    if hoist:
        chunk_idx_stat.value = index // chunk_size
        index.value -= chunk_idx_stat * chunk_size

    chunk_starts = list(range(0, n, chunk_size))
    for chunk_idx, chunk_start in enumerate(chunk_starts[1:], start=1):
        chunk_end = min(chunk_start + chunk_size, n)
        if hoist:
            with IfAll(chunk_idx_stat == chunk_idx):
                for j, item in enumerate(items[chunk_start:chunk_end]):
                    assign(temp_stats[j], item)
        else:
            with IfAll(index >= chunk_start, index < chunk_end):
                for j, item in enumerate(items[chunk_start:chunk_end]):
                    assign(temp_stats[j], item)
                index.value -= chunk_start
                chunk_idx_stat.value = chunk_idx
        if chunk_idx == 1:
            with Else:
                for j, item in enumerate(items[:chunk_size]):
                    assign(temp_stats[j], item)
                if not hoist:
                    chunk_idx_stat.value = 0

    for j in range(chunk_size):
        with IfAll(index == j):
            assign(temp_stats[j], input)

    for chunk_idx, chunk_start in enumerate(chunk_starts):
        chunk_end = min(chunk_start + chunk_size, n)
        with IfAll(chunk_idx_stat == chunk_idx):
            for j, item in enumerate(items[chunk_start:chunk_end]):
                assign(item, temp_stats[j])


def into_tuple[T: Checkable | HousingType](item: T | tuple[T, ...]) -> tuple[T, ...]:
    return item if isinstance(item, tuple) else (item,)


def assert_same_widths(items: Iterable[Sequence[Any]]) -> int:
    width = len(next(iter(items), ()))
    for item in items:
        if len(item) != width:
            raise ValueError('All items must have the same width')
    return width


def cheap_read(
    *,
    items: Sequence[Checkable | HousingType | tuple[Checkable | HousingType, ...]],
    index: Editable,
    output: Editable | tuple[Editable, ...],
) -> None:
    normalized_items = [into_tuple(item) for item in items]
    normalized_output = into_tuple(output)
    if len(items) == 0:
        raise ValueError('Cannot read from an empty list')
    width = assert_same_widths((*normalized_items, normalized_output))
    if width > 12:
        raise ValueError(f'Tuple width {width} exceeds the supported maximum of 12')

    cheap_read_inner(
        items=normalized_items,
        index=index,
        output=normalized_output,
    )


def cheap_write(
    *,
    items: Sequence[Editable | tuple[Editable, ...]],
    index: Editable,
    input: Checkable | HousingType | tuple[Checkable | HousingType, ...],
) -> None:
    normalized_items = [into_tuple(item) for item in items]
    normalized_input = into_tuple(input)
    if len(items) == 0:
        raise ValueError('Cannot write to an empty list')
    width = assert_same_widths((*normalized_items, normalized_input))
    if width > 12:
        raise ValueError(f'Tuple width {width} exceeds the supported maximum of 12')

    cheap_write_inner(
        items=normalized_items,
        index=index,
        input=normalized_input,
    )
