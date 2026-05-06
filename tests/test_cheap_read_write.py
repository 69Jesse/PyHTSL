"""cheap_read / cheap_write across widths and lengths.

Verifies the correct slot is read from / written to for several (width, length)
pairs that exercise both special-case branches (len <= 4) and the recursive
chunked branch (len > 4 for reads, len > 25 for writes).

The slow-path tests use letter names (`a, b, ..., z, aa, ab, ...`) so the
substitution-based shortcut in cheap_read does NOT kick in — those names don't
form an arithmetic-sequence pattern. The fast-path / shortcut is exercised
separately in the second half of the file.
"""

import random

from helpers import expect_exception

from pyhtsl import Container, ExecutionContext, GlobalStat, PlayerStat
from pyhtsl.expression.binary_expression import BinaryExpression
from pyhtsl.expression.condition.conditional_expression import ConditionalExpression
from pyhtsl.ext.cheap_read_write import cheap_read, cheap_write


def letter_name(i: int) -> str:
    """0 -> 'a', 1 -> 'b', ..., 25 -> 'z', 26 -> 'aa', 27 -> 'ab', ..., 51 -> 'az', 52 -> 'ba'.

    Spreadsheet-column-style encoding. Used to defeat cheap_read's fast path,
    which only triggers when names form `prefix + format(start + i, ',') + suffix`.
    """
    parts = []
    n = i
    while True:
        parts.append(chr(ord('a') + n % 26))
        n = n // 26 - 1
        if n < 0:
            break
    return ''.join(reversed(parts))


def sample_targets(length: int) -> list[int]:
    return random.sample(range(length), min(20, length))


def value_at(i: int, k: int) -> int:
    return i * 1000 + k + 1  # nonzero so a read into a default-0 stat is detectable


# --- cheap_read slow-path: reads return the targeted item ---

for length in (1, 10, 100):
    for width in (1, 3):
        with ExecutionContext(ignore_action_limits=True) as ctx:
            sources = [
                tuple(
                    PlayerStat(letter_name(i * width + k)).as_long()
                    for k in range(width)
                )
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
                tuple(
                    PlayerStat(letter_name(i * width + k)).as_long()
                    for k in range(width)
                )
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


# --- cheap_read fast-path: shortcut via placeholder substitution ---
#
# When item names form `prefix + format(start + i, ',') + suffix`, cheap_read
# emits a constant-size sequence of BinaryExpressions instead of a chunked
# IfAll/Else cascade. Each fast-path read emits per column:
#   - n_k.value = index [+ offset]                   (1 BE)
#   - p_k.value = '%var.<scope>/<prefix>'            (1 BE, only if prefix non-empty)
#   - tmp_str_k.value = template                     (1 BE)
#   - tmp_str_k.set(tmp_str_k, intentional)          (1 BE: chain resolver)
#   - output[k].value = tmp_str_k                    (1 BE)
# So 5 BEs per column with non-empty prefix, 4 BEs per column with empty prefix.

# Width=1, non-empty prefix, simple indexing → 5 BinaryExpressions, no conditionals.
with Container() as container:
    sources = [PlayerStat(f'src{i}').as_long() for i in range(10)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 5, counts


# Width=1, empty prefix (names are just digits) → 4 BinaryExpressions.
with Container() as container:
    sources = [PlayerStat(f'{i}').as_long() for i in range(10)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 4, counts


# Width=3 Mode A (shared prefix, flat numbering) → 15 BinaryExpressions.
with Container() as container:
    items = [
        tuple(PlayerStat(f'a{i * 3 + k}').as_long() for k in range(3))
        for i in range(10)
    ]
    idx = PlayerStat('idx').as_long()
    o = tuple(PlayerStat(f'o{k}').as_long() for k in range(3))
    cheap_read(items=items, index=idx, output=o)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 15, counts


# Width=3 Mode B (per-column independent prefix) → 15 BinaryExpressions.
with Container() as container:
    items = [
        (
            PlayerStat(f'aaa{i}').as_long(),
            PlayerStat(f'bbb{i}').as_long(),
            PlayerStat(f'ccc{i}').as_long(),
        )
        for i in range(10)
    ]
    idx = PlayerStat('idx').as_long()
    o = tuple(PlayerStat(f'o{k}').as_long() for k in range(3))
    cheap_read(items=items, index=idx, output=o)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 15, counts


# GlobalStat fast path → 5 BinaryExpressions (same shape as PlayerStat).
with Container() as container:
    sources = [GlobalStat(f'gsrc{i}').as_long() for i in range(10)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 5, counts


# Middle-digit increment (`a101a, a111a, a121a, ...`) → still fast path.
with Container() as container:
    sources = [PlayerStat(f'a1{i}1a').as_long() for i in range(10)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 5, counts


# Comma boundary: names cross 999 -> 1,000 with comma formatting -> fast path.
with Container() as container:
    sources = [PlayerStat(f'a{i:,}').as_long() for i in range(999, 1010)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 5, counts


# Comma boundary correctness: substitution applies comma formatting (mirrors
# HTSL behavior), so reading items[i] for i straddling the 999/1,000 boundary
# resolves to the correct stat.
for _target in (0, 1, 4, 10):  # 0 -> a999, 1 -> a1,000, 10 -> a1,009
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [PlayerStat(f'a{i:,}').as_long() for i in range(999, 1010)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 1_000_000 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_comma(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 1_000_000 + _t, (got, _t)

        ctx.assert_all(check_comma)


# No-comma names crossing 1000 boundary: pattern detection bails (since
# format(1000, ',') == '1,000' != '1000') -> falls back to slow path.
with Container() as container:
    sources = [PlayerStat(f'a{i}').as_long() for i in range(999, 1010)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 2, counts
assert counts[BinaryExpression] > 5, counts
assert counts[ConditionalExpression] > 1, counts


# Mixing PlayerStat and GlobalStat in the same items -> fast-path bails.
with Container() as container:
    sources = [
        PlayerStat('mix0').as_long(),
        GlobalStat('mix1').as_long(),
        PlayerStat('mix2').as_long(),
    ]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 2, counts
assert ConditionalExpression in counts, counts


# Plain integer literals as items -> not stats at all -> slow path.
with Container() as container:
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=[10, 20, 30, 40, 50], index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 2, counts
assert ConditionalExpression in counts, counts


# --- Fast-path correctness via ExecutionContext (n < 1000) ---
#
# Each test uses a single cheap_read per ExecutionContext. The fast path's
# writes are unconditional, so stacking multiple cheap_read calls in a loop
# would let the dead-store eliminator merge them — that's the optimizer
# working correctly under the test's opaque-callback pattern (the slow path
# survives the same pattern only because its writes are inside IfAll). For a
# faithful single-read test, isolate each call in its own context.


# Width=1, PlayerStat, prefix='src', start=0
for _target in (0, 3, 7, 9):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [PlayerStat(f'src{i}').as_long() for i in range(10)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 100 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_w1_player(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 100 + _t, (got, _t)

        ctx.assert_all(check_w1_player)


# Width=1, GlobalStat
for _target in (0, 4, 9):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [GlobalStat(f'gsrc{i}').as_long() for i in range(10)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 200 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_w1_global(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 200 + _t, (got, _t)

        ctx.assert_all(check_w1_global)


# Width=3, Mode B (per-column prefixes)
for _target in (0, 2, 5, 7):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _items = [
            (
                PlayerStat(f'aaa{i}').as_long(),
                PlayerStat(f'bbb{i}').as_long(),
                PlayerStat(f'ccc{i}').as_long(),
            )
            for i in range(8)
        ]
        for _i, _row in enumerate(_items):
            for _k, _s in enumerate(_row):
                ctx.put(_s, _i * 10 + _k)
        _idx = PlayerStat('idx').as_long()
        _outputs = tuple(PlayerStat(f'o{k}').as_long() for k in range(3))
        _idx.value = _target
        cheap_read(items=_items, index=_idx, output=_outputs)

        def check_w3_modeB(
            _t: int = _target,
            _outs: tuple[PlayerStat, ...] = _outputs,
        ) -> None:
            for k in range(3):
                got = int(ctx.get(_outs[k]))
                assert got == _t * 10 + k, (got, _t, k)

        ctx.assert_all(check_w3_modeB)


# Width=3, Mode A (shared prefix, flat numbering)
for _target in (0, 3, 7):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _items = [
            tuple(PlayerStat(f'm{i * 3 + k}').as_long() for k in range(3))
            for i in range(8)
        ]
        for _i, _row in enumerate(_items):
            for _k, _s in enumerate(_row):
                ctx.put(_s, _i * 100 + _k)
        _idx = PlayerStat('idx').as_long()
        _outputs = tuple(PlayerStat(f'o{k}').as_long() for k in range(3))
        _idx.value = _target
        cheap_read(items=_items, index=_idx, output=_outputs)

        def check_w3_modeA(
            _t: int = _target,
            _outs: tuple[PlayerStat, ...] = _outputs,
        ) -> None:
            for k in range(3):
                got = int(ctx.get(_outs[k]))
                assert got == _t * 100 + k, (got, _t, k)

        ctx.assert_all(check_w3_modeA)


# Middle-digit pattern correctness ('a1<n>1a')
for _target in (0, 3, 6, 9):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [PlayerStat(f'a1{i}1a').as_long() for i in range(10)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 7000 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_middle(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 7000 + _t, (got, _t)

        ctx.assert_all(check_middle)


# Non-zero start (offset != 0): items 'p5'..'p14', logical index 0..9
for _target in (0, 3, 9):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [PlayerStat(f'p{i}').as_long() for i in range(5, 15)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 500 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_offset(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 500 + _t, (got, _t)

        ctx.assert_all(check_offset)


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
