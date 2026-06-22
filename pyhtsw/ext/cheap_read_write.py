import math
from collections.abc import Iterable, Sequence
from typing import Any

from ..actions.conditional.statements import Else, IfAll, IfAny
from ..editable import Checkable, Editable, HousingType
from ..internal_type import InternalType
from ..stats.global_stat import GlobalStat
from ..stats.player_stat import PlayerStat
from ..stats.stat import Stat
from .set_string import set_string

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


def assert_same_widths(items: Iterable[Sequence[Any]]) -> int:
    width = len(next(iter(items), ()))
    for item in items:
        if len(item) != width:
            raise ValueError('All items must have the same width')
    return width


def _common_prefix(names: Sequence[str]) -> str:
    if not names:
        return ''
    p = names[0]
    for n in names[1:]:
        i = 0
        while i < len(p) and i < len(n) and p[i] == n[i]:
            i += 1
        p = p[:i]
        if not p:
            break
    return p


def _common_suffix(names: Sequence[str]) -> str:
    if not names:
        return ''
    s = names[0]
    for n in names[1:]:
        i = 0
        while i < len(s) and i < len(n) and s[-1 - i] == n[-1 - i]:
            i += 1
        s = s[len(s) - i :] if i else ''
        if not s:
            break
    return s


def _parse_comma_int(text: str) -> int | None:
    """Return n if text == format(n, ',') for some non-negative int, else None."""
    if not text:
        return None
    raw = text.replace(',', '')
    if not raw.isdigit():
        return None
    n = int(raw)
    if format(n, ',') != text:
        return None
    return n


def _detect_linear_run(
    names: Sequence[str],
    expected_step: int,
) -> tuple[str, str, int] | None:
    """If every name == prefix + format(start + expected_step*i, ',') + suffix
    using the longest common prefix/suffix, return (prefix, suffix, start)."""
    if len(names) < 2:
        return None
    prefix = _common_prefix(names)
    suffix = _common_suffix(names)
    if '%' in prefix or '%' in suffix or '"' in prefix or '"' in suffix:
        return None
    suffix_len = len(suffix)
    middles: list[str] = []
    for name in names:
        if len(prefix) + suffix_len > len(name):
            return None
        middle = (
            name[len(prefix) : len(name) - suffix_len]
            if suffix_len
            else name[len(prefix) :]
        )
        middles.append(middle)
    start = _parse_comma_int(middles[0])
    if start is None:
        return None
    for i, mid in enumerate(middles):
        if mid != format(start + expected_step * i, ','):
            return None
    return prefix, suffix, start


# (stat_class, prefix, suffix, coeff, offset)
type ColumnInfo = tuple[type[Stat], str, str, int, int]


def _uniform_stat_class(stats: Sequence[Any]) -> type[Stat] | None:
    """Return the shared class if every item is the same PlayerStat/GlobalStat, else None."""
    if not stats:
        return None
    cls = type(stats[0])
    if cls is not PlayerStat and cls is not GlobalStat:
        return None
    for s in stats[1:]:
        if type(s) is not cls:
            return None
    return cls


def _detect_pattern_a(
    items: Sequence[Sequence[Checkable | HousingType]],
) -> list[ColumnInfo] | None:
    """Mode A: shared prefix/suffix/class across all positions; flat numbering.

    items[i][k]'s name == prefix + format(start + i*width + k, ',') + suffix.
    """
    width = len(items[0])
    flat = [items[i][k] for i in range(len(items)) for k in range(width)]
    cls = _uniform_stat_class(flat)
    if cls is None:
        return None
    info = _detect_linear_run(
        [s.name for s in flat if isinstance(s, Stat)],
        expected_step=1,
    )
    if info is None:
        return None
    prefix, suffix, start = info
    return [(cls, prefix, suffix, width, start + k) for k in range(width)]


def _detect_pattern_b(
    items: Sequence[Sequence[Checkable | HousingType]],
) -> list[ColumnInfo] | None:
    """Mode B: per-column independent; within each column step=1."""
    width = len(items[0])
    results: list[ColumnInfo] = []
    for k in range(width):
        column = [items[i][k] for i in range(len(items))]
        cls = _uniform_stat_class(column)
        if cls is None:
            return None
        info = _detect_linear_run(
            [s.name for s in column if isinstance(s, Stat)],
            expected_step=1,
        )
        if info is None:
            return None
        prefix, suffix, start = info
        results.append((cls, prefix, suffix, 1, start))
    return results


def _detect_pattern(
    items: Sequence[Sequence[Checkable | HousingType]],
) -> list[ColumnInfo] | None:
    if len(items) < 2:
        return None
    return _detect_pattern_a(items) or _detect_pattern_b(items)


_FAST_READ_NAMES = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def _emit_fast_read(
    *,
    pattern: list[ColumnInfo],
    index: Editable,
    output: Sequence[Editable],
) -> None:
    width = len(pattern)
    if 3 * width > len(_FAST_READ_NAMES):
        raise ValueError(f'cheap_read fast path: width {width} too large')
    n_stats = [PlayerStat(_FAST_READ_NAMES[k]).as_long() for k in range(width)]
    tmp_str_stats = [PlayerStat(_FAST_READ_NAMES[width + k]) for k in range(width)]
    p_stats = [PlayerStat(_FAST_READ_NAMES[2 * width + k]) for k in range(width)]

    for k, (cls, prefix, suffix, coeff, offset) in enumerate(pattern):
        scope = cls.right_side_keyword()
        n_k = n_stats[k]
        tmp_str_k = tmp_str_stats[k]

        if coeff == 1:
            n_k.value = index if offset == 0 else index + offset
        else:
            n_k.value = index * coeff if offset == 0 else index * coeff + offset

        if prefix:
            p_k = p_stats[k]
            p_k.value = f'%var.{scope}/{prefix}'
            template = f'%var.player/{p_k.name}%%var.player/{n_k.name}%{suffix}%'
        else:
            template = f'%var.{scope}/%var.player/{n_k.name}%{suffix}%'

        set_string(tmp_str_k, template)
        tmp_str_k.set(tmp_str_k, is_intentional_self_assignment=True)
        output[k].value = tmp_str_k


type MaybeSequence[T] = T | Sequence[T]


def into_sequence[T](item: MaybeSequence[T]) -> Sequence[T]:
    return item if isinstance(item, Sequence) else (item,)


def cheap_read(
    *,
    items: Sequence[MaybeSequence[Checkable | HousingType]],
    index: Editable,
    output: MaybeSequence[Editable],
) -> None:
    items = [into_sequence(item) for item in items]
    output = into_sequence(output)

    if len(items) == 0:
        raise ValueError('Cannot read from an empty list')
    width = assert_same_widths((*items, output))
    if width > 12:
        raise ValueError(f'Tuple width {width} exceeds the supported maximum of 12')

    pattern = _detect_pattern(items)
    if pattern is not None:
        _emit_fast_read(pattern=pattern, index=index, output=output)
        return

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


def cheap_write(
    *,
    items: Sequence[MaybeSequence[Editable]],
    index: Editable,
    input: MaybeSequence[Checkable | HousingType],
) -> None:
    items = [into_sequence(item) for item in items]
    input = into_sequence(input)

    if len(items) == 0:
        raise ValueError('Cannot write to an empty list')
    width = assert_same_widths((*items, input))
    if width > 12:
        raise ValueError(f'Tuple width {width} exceeds the supported maximum of 12')

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
