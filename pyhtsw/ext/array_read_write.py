import math
from collections.abc import Iterable, Sequence
from typing import Any, NamedTuple

from pyhtsw.actions.flow import Else, IfAll, IfAny
from pyhtsw.editable import Checkable, Editable, HousingType, NumericHousingType
from pyhtsw.ext.set_string import set_string
from pyhtsw.internal_type import InternalType
from pyhtsw.stats.global_stat import GlobalStat
from pyhtsw.stats.player_stat import PlayerStat
from pyhtsw.stats.stat import Stat

__all__ = (
    'array_read',
    'array_write',
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
        PlayerStat(f'tmp{i * width + k}')._as_type(InternalType.from_value(template[k]))
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


def _fast_names_pool(pattern: list[ColumnInfo]) -> str:
    excluded = {
        prefix
        for cls, prefix, _suffix, _coeff, _offset in pattern
        if cls is PlayerStat and len(prefix) == 1
    }
    return ''.join(c for c in _FAST_READ_NAMES if c not in excluded)


def _get_or_bake_composed_prefix(value: str, pool: str) -> PlayerStat:
    from pyhtsw.compiler.container import get_current_container

    container = get_current_container()
    top_ref = container.blocks[0].expressions
    for ctx in container.contexts:
        if ctx.parent_expression is None:
            top_ref = ctx.expressions_ref
    cache: dict[tuple[int, str], str] = container.__dict__.setdefault(
        '_composed_prefix_cache',
        {},
    )
    key = (id(top_ref), value)
    name = cache.get(key)
    if name is not None and name in pool:
        return PlayerStat(name)
    used = {n for (ref, _v), n in cache.items() if ref == id(top_ref)}
    name = next((c for c in reversed(pool) if c not in used), None)
    if name is None:
        # Exhausted: reuse the last name, dropping whichever entry held it so
        # no later read resolves a clobbered prefix.
        name = pool[-1]
        for cache_key, cached_name in list(cache.items()):
            if cache_key[0] == id(top_ref) and cached_name == name:
                del cache[cache_key]
    stat = PlayerStat(name)
    stat.value = value
    if not _in_nested_container():
        cache[key] = name
    return stat


def _direct_index_name(
    index: Editable,
    *,
    prefix: str,
    tail_length: int,
    coeff: int,
    offset: int,
    taken: str,
) -> str | None:
    if coeff != 1 or offset != 0:
        return None
    if type(index) is not PlayerStat:
        return None
    if index.internal_type is not InternalType.LONG or index.auto_unset:
        return None
    name = index.name
    # %var.player/<p>% + %var.player/<name>% + tail of 32 chars total.
    if 14 + 13 + len(name) + tail_length > 32:
        return None
    if name == prefix or name in taken:
        return None
    return name


def _column_internal_type(
    items: Sequence[Sequence[Checkable | HousingType]],
    k: int,
) -> InternalType:
    first = items[0][k]
    if not isinstance(first, Stat):
        return InternalType.ANY
    for item in items:
        slot = item[k]
        if not isinstance(slot, Stat) or slot.internal_type is not first.internal_type:
            return InternalType.ANY
    return first.internal_type


def _column_fallback(
    items: Sequence[Sequence[Checkable | HousingType]],
    k: int,
) -> str | None:
    """The rendered fallback every slot of column ``k`` agrees on, if any."""
    first = items[0][k]
    if not isinstance(first, Stat) or first.fallback_value is None:
        return None
    for item in items:
        slot = item[k]
        if not isinstance(slot, Stat) or slot.fallback_value != first.fallback_value:
            return None
    formatted = first.get_formatted_fallback_value()
    if not formatted or '%' in formatted or ' ' in formatted:
        return None
    return formatted


def _composed_reference_parts(
    cls: type[Stat],
    prefix: str,
    suffix: str,
    column_type: InternalType,
    fallback: str | None = None,
) -> tuple[str, str]:
    if column_type is InternalType.LONG:
        return f'%stat.{cls.right_side_keyword()}/{prefix}', f'{suffix}%L'
    if column_type is InternalType.DOUBLE:
        return f'%var.{cls.right_side_keyword()}/{prefix}', f'{suffix} 0%D'
    tail = f' {fallback}' if fallback is not None else ''
    return f'%var.{cls.right_side_keyword()}/{prefix}', f'{suffix}{tail}%'


def _emit_fast_read(
    *,
    pattern: list[ColumnInfo],
    index: Editable,
    output: Sequence[Editable],
    column_types: Sequence[InternalType],
    column_fallbacks: Sequence[str | None] | None = None,
) -> None:
    width = len(pattern)
    names = _fast_names_pool(pattern)
    if 2 * width > len(names):
        raise ValueError(f'array_read fast path: width {width} too large')
    tmp_str_stats = [PlayerStat(names[k]) for k in range(width)]
    n_stats = [
        PlayerStat(names[width + k]).as_long().with_auto_unset(False)
        for k in range(width)
    ]

    for k, (cls, prefix, suffix, coeff, offset) in enumerate(pattern):
        tmp_str_k = tmp_str_stats[k]

        # The scope head always rides in the prefix variable - even when the
        # item names have no shared prefix. A literal `%var.player/` written
        # inline would pair its `%` with the counter's and be eaten. Its value
        # is constant, so it costs one action per list, not per read.
        p_value, tail = _composed_reference_parts(
            cls,
            prefix,
            suffix,
            column_types[k],
            column_fallbacks[k] if column_fallbacks is not None else None,
        )
        p_k = _get_or_bake_composed_prefix(p_value, names)

        counter_name = _direct_index_name(
            index,
            prefix=prefix,
            tail_length=len(tail),
            coeff=coeff,
            offset=offset,
            taken=p_k.name + tmp_str_k.name,
        )
        if counter_name is None:
            # The copy also normalizes auto-unset: a zero index would
            # otherwise vanish from the composed name.
            n_k = n_stats[k]
            if coeff == 1:
                n_k.value = index if offset == 0 else index + offset
            else:
                n_k.value = index * coeff if offset == 0 else index * coeff + offset
            counter_name = n_k.name

        template = f'%var.player/{p_k.name}%%var.player/{counter_name}%{tail}'
        set_string(tmp_str_k, template)
        # A bare single-placeholder right side resolves in two passes, so this
        # consumes the composed reference and assigns the value in one action.
        # Widening the left side to ANY stops a typed coercion from quoting it
        # into one-pass string semantics.
        output[k]._as_type(InternalType.ANY).value = tmp_str_k


type MaybeSequence[T] = T | Sequence[T]


def into_sequence[T](item: MaybeSequence[T]) -> Sequence[T]:
    if isinstance(item, str):
        # A string is itself a Sequence; treat it as one value, not width
        # many characters.
        return (item,)  # type: ignore[return-value]
    return item if isinstance(item, Sequence) else (item,)


# Housing's per-action-list caps; a conditional's branch gets its own budget.
_BE_LIMIT = 25

_HI_KEY = 500


def _in_nested_container() -> bool:
    from pyhtsw.compiler.container import get_current_container

    return any(
        ctx.parent_expression is not None for ctx in get_current_container().contexts
    )


class _FastWriteShape(NamedTuple):
    chunk: int
    chunks: int
    table: int
    split: bool
    mid: int


def _fast_write_shape(n: int, width: int, chunk: int) -> _FastWriteShape:
    table = min(chunk, n)
    return _FastWriteShape(
        chunk=chunk,
        chunks=math.ceil(n / chunk),
        table=table,
        split=table * width + (table - 1) > _BE_LIMIT,
        mid=(table + 1) // 2,
    )


def _fast_write_costs(n: int, width: int, chunk: int) -> tuple[int, int]:
    s = _fast_write_shape(n, width, chunk)
    scatter = s.table * width + (s.table - 1)

    setup = 5 * width + 2 * width + width + 1  # read, diff, prefixes, counter
    if s.chunks >= 2:
        setup += 4  # counter -> index mod chunk
    if s.split:
        setup += 3 * width + 2  # payload split
    if not s.split:
        setup += scatter
    if s.chunks == 1 and not s.split:
        setup += n * width  # inline blits

    runs = [setup]
    if s.chunks == 1 and s.split:
        runs.append(n * width)  # blits after the scatter conditional

    # Worst-case convention: the enclosing action list is already full, so
    # every top-level run costs its own ceil(run / 25) wrapper conditionals.
    wrappers = sum(math.ceil(run / _BE_LIMIT) for run in runs)

    conditionals = wrappers + (1 if s.split else 0)
    if s.chunks == 2:
        conditionals += 1
    elif s.chunks >= 3:
        conditionals += s.chunks

    expressions = sum(runs)
    if s.split:
        expressions += scatter + 1  # the high branch's counter offset
    if s.chunks >= 2:
        expressions += n * width
    return conditionals, expressions


def _emit_fast_write(
    *,
    pattern: list[ColumnInfo],
    items: Sequence[Sequence[Editable]],
    index: Editable,
    input: Sequence[Checkable | NumericHousingType],
    chunk: int,
) -> None:
    from pyhtsw.directives.preserved import Preserved
    from pyhtsw.directives.strict_order import StrictOrder
    from pyhtsw.stats.temporary_stat import TemporaryStat

    n = len(items)
    width = len(pattern)
    s = _fast_write_shape(n, width, chunk)

    pool = _fast_names_pool(pattern)
    if 4 * width + 1 > len(pool):
        raise ValueError(f'array_write fast path: width {width} too large')
    # `_emit_fast_read` claims pool[:3 * width] for itself.
    q_stats = [PlayerStat(pool[3 * width + k]) for k in range(width)]
    d = PlayerStat(pool[4 * width]).as_long().with_auto_unset(False)
    lo = [PlayerStat(f'hw{k}_0').as_long() for k in range(width)]
    hi = [PlayerStat(f'hw{k}_{_HI_KEY}').as_long() for k in range(width)]
    # The un-rebaked part of the table may be unset (first call), so a blit
    # needs the explicit 0 fallback: an empty-string resolve is fatal in-game.
    slots = [
        [PlayerStat(f'sw{j}_{k}', fallback_value=0) for k in range(width)]
        for j in range(s.table)
    ]
    t = TemporaryStat().as_long()

    def bake(j: int) -> None:
        for k in range(width):
            # Exactly 32 characters, the most one assignment holds. The
            # trailing `L` rides along unresolved and lands on the number the
            # one-hot yields, which is what lets the blit read it back: that
            # number is rendered with thousands separators, and only the `...L`
            # form strips them before parsing.
            set_string(
                slots[j][k],
                f'%var.player/{q_stats[k].name}%%var.player/{d.name}% 0%L',
            )

    def blit(chunk_idx: int) -> None:
        start = chunk_idx * chunk
        for j, item in enumerate(items[start : start + chunk]):
            for k in range(width):
                # A slot holds the *unresolved* one-hot reference, so the blit
                # has to resolve twice. Only a bare `%...%` right-hand side does
                # that; the quoted form a typed left side would coerce it into
                # stops after one pass and yields the text. Widening the left
                # side to ANY suppresses that coercion.
                item[k]._as_type(InternalType.ANY).value += slots[j][k]

    with StrictOrder(), Preserved():
        # lo_k = diff_k = input[k] - items[index][k], via one composed read.
        _emit_fast_read(
            pattern=pattern,
            index=index,
            output=lo,
            column_types=[InternalType.LONG] * width,
        )
        for k in range(width):
            lo[k].value *= -1
            lo[k].value += input[k]
        d.value = index
        if s.chunks >= 2:
            # d -> p = index mod chunk.
            d.value //= chunk
            d.value *= chunk
            d.value -= index
            d.value *= -1
        if s.split:
            # Route the diff to the rebaked half's payload key.
            t.value = d
            t.value //= s.mid
            for k in range(width):
                hi[k].value = lo[k]
                hi[k].value *= t
                lo[k].value -= hi[k]
        for k in range(width):
            q_stats[k].value = f'%var.player/hw{k}_'

        if s.split:
            # Rebake only the half of the table containing p.
            with IfAll(d <= s.mid - 1):
                for j in range(s.mid):
                    bake(j)
                    if j != s.mid - 1:
                        d.value -= 1
            with Else:
                d.value += _HI_KEY - s.mid
                for j in range(s.mid, s.table):
                    bake(j)
                    if j != s.table - 1:
                        d.value -= 1
        else:
            for j in range(s.table):
                bake(j)
                if j != s.table - 1:
                    d.value -= 1

        if s.chunks == 1:
            blit(0)
        elif s.chunks == 2:
            # The else is the exact second range for in-range indices, so this
            # single conditional covers both chunks for free.
            with IfAll(index <= chunk - 1):
                blit(0)
            with Else:
                blit(1)
        else:
            for c in range(s.chunks):
                start = c * chunk
                with IfAll(index >= start, index <= start + chunk - 1):
                    blit(c)


def _slow_write_costs(n: int, width: int) -> tuple[int, int]:
    best: tuple[int, int] = (n, n * width)
    for hoist in (False, True):
        max_cs = (25 if hoist else 23) // width
        for cs in range(1, min(max_cs, n - 1) + 1):
            chunks = math.ceil(n / cs)
            conditionals = 2 * chunks - 1 + cs
            bookkeeping = 0 if hoist else 2
            expressions = (
                (3 if hoist else 0)
                + (chunks - 1) * (cs * width + bookkeeping)
                + cs * width
                + (0 if hoist else 1)
                + cs * width
                + n * width
            )
            if (conditionals, expressions) < best:
                best = (conditionals, expressions)
    return best


def _fast_write_plan(
    *,
    items: Sequence[Sequence[Editable]],
    n: int,
    width: int,
) -> tuple[list[ColumnInfo], int] | None:
    if not all(
        isinstance(slot, Stat) and slot.internal_type is InternalType.LONG
        for item in items
        for slot in item
    ):
        return None
    pattern = _detect_pattern(items)
    if pattern is None:
        return None
    # The fast path keys its one-hot lookups on composed names in the `hw`
    # namespace (and stage slots in `sw`/`tmp` ones). Items living in those
    # namespaces would collide with the machinery, so they take the cascade.
    if any(
        prefix.startswith(('hw', 'sw', 'tmp'))
        for _cls, prefix, _suffix, _coeff, _offset in pattern
    ):
        return None

    best: tuple[tuple[int, int], int] | None = None
    for chunk in range(1, _BE_LIMIT // width + 1):
        cost = _fast_write_costs(n, width, chunk)
        if best is None or cost < best[0]:
            best = (cost, chunk)
    if best is None:
        return None
    cost, chunk = best
    if cost >= _slow_write_costs(n, width):
        return None
    if _in_nested_container():
        # Inside a conditional there is no room to grow: another conditional
        # cannot be nested, and neither can a wrapper. The emission must have
        # no REAL conditionals (worst-case cost counts wrappers, which do not
        # apply inside a branch) and fit the branch's single action list.
        shape = _fast_write_shape(n, width, chunk)
        if shape.split or shape.chunks > 1 or cost[1] > _BE_LIMIT:
            return None
    return pattern, chunk


def _staged_write_costs(n: int, width: int, cs: int) -> tuple[int, int]:
    chunks = math.ceil(n / cs)
    setup = 6 + width  # c*, p, and per-column counter bases
    loads = 3 * cs * width - width  # bake + consume per slot, walk between
    top_level = setup + loads
    # Worst-case convention: the whole top-level run is wrapped.
    wrappers = math.ceil(top_level / _BE_LIMIT)
    conditionals = wrappers + cs + chunks
    expressions = top_level + cs * width + n * width
    return conditionals, expressions


def _staged_write_plan(
    *,
    items: Sequence[Sequence[Editable]],
    n: int,
    width: int,
) -> tuple[list[ColumnInfo], list[InternalType], int] | None:
    pattern = _detect_pattern(items)
    if pattern is None:
        return None
    if any(
        prefix.startswith(('hw', 'sw', 'tmp'))
        for _cls, prefix, _suffix, _coeff, _offset in pattern
    ):
        return None
    column_types = [_column_internal_type(items, k) for k in range(width)]
    # Mixed columns have no single comma-safe reference form.
    if any(t is InternalType.ANY for t in column_types):
        return None

    best: tuple[tuple[int, int], int] | None = None
    for cs in range(1, _BE_LIMIT // width + 1):
        cost = _staged_write_costs(n, width, cs)
        if best is None or cost < best[0]:
            best = (cost, cs)
    if best is None:
        return None
    cost, cs = best
    if cost >= _slow_write_costs(n, width):
        return None
    if _in_nested_container():
        return None
    return pattern, column_types, cs


def _emit_staged_write(
    *,
    pattern: list[ColumnInfo],
    column_types: Sequence[InternalType],
    items: Sequence[Sequence[Editable]],
    index: Editable,
    input: Sequence[Checkable | HousingType],
    cs: int,
) -> None:
    from pyhtsw.directives.strict_order import StrictOrder
    from pyhtsw.stats.temporary_stat import TemporaryStat

    n = len(items)
    width = len(pattern)
    chunks = math.ceil(n / cs)

    pool = _fast_names_pool(pattern)
    if 2 * width > len(pool):
        raise ValueError(f'array_write staged path: width {width} too large')
    counters = [
        PlayerStat(pool[k]).as_long().with_auto_unset(False) for k in range(width)
    ]
    bakers = [PlayerStat(pool[width + k]) for k in range(width)]
    staged = [[TemporaryStat() for _ in range(width)] for _ in range(cs)]
    chunk_no = TemporaryStat().as_long()
    pos = TemporaryStat().as_long()
    base = TemporaryStat().as_long()

    with StrictOrder():
        chunk_no.value = index
        chunk_no.value //= cs
        base.value = chunk_no
        base.value *= cs
        pos.value = index
        pos.value -= base

        for k, (cls, prefix, suffix, coeff, offset) in enumerate(pattern):
            p_value, tail = _composed_reference_parts(
                cls,
                prefix,
                suffix,
                column_types[k],
            )
            p_k = _get_or_bake_composed_prefix(p_value, pool)
            d_k = counters[k]
            d_k.value = base
            if coeff != 1:
                d_k.value *= coeff
            if offset != 0:
                d_k.value += offset
            template = f'%var.player/{p_k.name}%%var.player/{d_k.name}%{tail}'
            for j in range(cs):
                set_string(bakers[k], template)
                staged[j][k]._as_type(InternalType.ANY).value = bakers[k]
                if j != cs - 1:
                    d_k.value += coeff

        for j in range(cs):
            with IfAll(pos == j):
                for k in range(width):
                    if column_types[k] is InternalType.STRING:
                        # A string-typed left side copies in one quoted pass,
                        # so a value that looks like a placeholder is not
                        # resolved a second time.
                        staged[j][k]._as_type(InternalType.STRING).value = input[k]
                    else:
                        staged[j][k].value = input[k]

        for c in range(chunks):
            start = c * cs
            size = min(cs, n - start)
            with IfAll(index >= start, index <= start + size - 1):
                for j in range(size):
                    for k in range(width):
                        item = items[start + j][k]
                        if column_types[k] is InternalType.STRING:
                            # Typed store: quoted one-pass, verbatim text.
                            item.value = staged[j][k]
                        else:
                            # ANY-widened store: the bare read returns the
                            # temp's raw numeric value - exact, and without
                            # the literal L/D tail a quoted typed read would
                            # keep as text.
                            item._as_type(InternalType.ANY).value = staged[j][k]


def array_read(
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
        _emit_fast_read(
            pattern=pattern,
            index=index,
            output=output,
            column_types=[_column_internal_type(items, k) for k in range(width)],
            column_fallbacks=[_column_fallback(items, k) for k in range(width)],
        )
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


def array_write(
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

    fast = _fast_write_plan(items=items, n=n, width=width)
    numeric_input = [value for value in input if not isinstance(value, str)]
    if fast is not None and len(numeric_input) == len(input):
        pattern, chunk = fast
        _emit_fast_write(
            pattern=pattern,
            items=items,
            index=index,
            input=numeric_input,
            chunk=chunk,
        )
        return

    staged = _staged_write_plan(items=items, n=n, width=width)
    if staged is not None:
        pattern, column_types, cs = staged
        _emit_staged_write(
            pattern=pattern,
            column_types=column_types,
            items=items,
            index=index,
            input=input,
            cs=cs,
        )
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


class StatArray[T: Editable](Sequence[MaybeSequence[T]]):
    """A fixed array of stats addressed by a runtime index.

    The object form of `array_read` / `array_write`: build it once from the
    slot stats (width-1 entries or same-width tuples) and use it like the
    array it is - `arr[3]` is compile-time access to the stat itself,
    `arr.read(index, output=...)` and `arr.write(index, input=...)` are the
    runtime-indexed operations, and iteration/len work, so it drops straight
    into anything that takes a holder list (e.g. `Queue(holders=arr, ...)`).
    """

    def __init__(self, items: Sequence[MaybeSequence[T]]) -> None:
        self.items: list[MaybeSequence[T]] = list(items)
        if not self.items:
            raise ValueError('StatArray needs at least one item')
        assert_same_widths([into_sequence(item) for item in self.items])

    @property
    def width(self) -> int:
        return len(into_sequence(self.items[0]))

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index):  # type: ignore[override]
        return self.items[index]

    def read(
        self,
        index: Editable,
        *,
        output: MaybeSequence[Editable],
    ) -> None:
        array_read(items=self.items, index=index, output=output)

    def write(
        self,
        index: Editable,
        *,
        input: MaybeSequence[Checkable | HousingType],
    ) -> None:
        array_write(items=self.items, index=index, input=input)
