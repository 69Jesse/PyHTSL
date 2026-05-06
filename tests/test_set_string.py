"""set_string: chunked string assignment under HTSL's 32-char source limit.

Covers:
- Short values: single direct set.
- Long values that are reducible via placeholders: chained self-concat,
  with each emitted line <= 32 chars source.
- Provably-impossible inputs raise (no placeholders, atom too big to fit).
- ExecutionContext correctness for short values, and the runtime rule
  (when substitution would exceed 32 chars, the literal source with
  placeholders is stored instead).
- Compile-time: emitting a string set with > 32 chars source raises.
"""

from helpers import expect_exception

from pyhtsl import Container, ExecutionContext, PlayerStat
from pyhtsl.expression.binary_expression import (
    SET_STRING_MAX_LENGTH,
    BinaryExpression,
)
from pyhtsl.ext.set_string import set_string

# --- short values: single direct set ---

with Container() as container:
    s = PlayerStat('s').as_string()
    set_string(s, 'hello world')

assert container.into_htsl() == 'var "s" = "hello world" true', container.into_htsl()


# value of exactly 32 chars: one line
with Container() as container:
    s = PlayerStat('s').as_string()
    value = 'A' * 32
    set_string(s, value)

assert container.into_htsl() == f'var "s" = "{value}" true', container.into_htsl()


# --- long value reduced by placeholders: chained self-concat ---

with Container() as container:
    s = PlayerStat('s').as_string()
    # Source > 32 chars but contains a placeholder:
    # "preamble%var.player/x%suffixsuffixsuffix" = 8 + 14 + 18 = 40 chars
    value = 'preamble%var.player/x%' + 'suffixsuffixsuffix'
    assert len(value) == 40
    set_string(s, value)

htsl = container.into_htsl()
lines = htsl.split('\n')
# Every line's set-string source (the part inside double quotes) must be <= 32.
for line in lines:
    assert '"' in line, line
    src = line.split('"', 2)[1]
    assert len(src) <= SET_STRING_MAX_LENGTH, (len(src), src, line)


# --- impossible: no placeholders, length > 32 ---

with expect_exception(ValueError):
    with Container() as container:
        s = PlayerStat('s').as_string()
        set_string(s, 'A' * 50)


# --- impossible: a single placeholder atom too long for any non-first chunk ---
#
# Self-ref of "%var.player/destination%" is 24 chars, leaving budget 8 for
# continuation chunks. After the first chunk fills with 32 literal chars, the
# placeholder atom (14 chars) lands in a continuation chunk where 14 > 8 —
# set_string must reject this.

with expect_exception(ValueError):
    with Container() as container:
        s = PlayerStat('destination').as_string()
        value = 'a' * 32 + '%var.player/y%'
        set_string(s, value)


# --- HTSL compile-time check: a direct set > 32 chars rejects at finalize ---
#
# The 32-char source check fires inside Container.__exit__ when each
# expression's into_htsl() runs during finalize. Use a small try/except so
# we can clean up the CONTAINERS stack if finalize raises mid-exit.

import pyhtsl.container as _container_mod  # noqa: E402

caught = False
try:
    with Container() as container:
        s = PlayerStat('s').as_string()
        s.value = 'A' * 33
except ValueError:
    caught = True
finally:
    # If finalize raised inside Container.__exit__, the container never got
    # popped from the global stack — restore it ourselves.
    while len(_container_mod.CONTAINERS) > 1:
        _container_mod.CONTAINERS.pop()
assert caught, 'expected ValueError for >32-char direct set'


# --- ExecutionContext: short value round-trip ---

with ExecutionContext() as ctx:
    s = PlayerStat('s').as_string()
    set_string(s, 'hello')

    def check_short() -> None:
        assert str(ctx.get(s)) == 'hello', ctx.get(s)

    ctx.assert_all(check_short)


# --- ExecutionContext: chained self-concat builds expanded value <= 32 ---

with ExecutionContext() as ctx:
    s = PlayerStat('s').as_string()
    x = PlayerStat('x').as_string()
    ctx.put(x, 'XYZ', ignore_warning=True)
    # Source 36 chars, but placeholder %var.player/x% (14 chars) substitutes
    # to "XYZ" (3 chars), so the expanded value is 36 - 14 + 3 = 25 chars,
    # well under 32. Chained self-concat should produce the right result.
    value = 'before%var.player/x%' + 'after_after_after'  # 6 + 14 + 17 = 37
    assert len(value) == 37
    set_string(s, value)
    expected = 'before' + 'XYZ' + 'after_after_after'  # 26 chars
    assert len(expected) <= SET_STRING_MAX_LENGTH

    def check_chained() -> None:
        assert str(ctx.get(s)) == expected, (ctx.get(s), expected)

    ctx.assert_all(check_chained)


# --- ExecutionContext: runtime rule fires when substitution would exceed 32 ---
#
# Set a stat to a literal whose substituted result would be > 32 chars.
# Per HTSL's runtime rule, the literal source (placeholders intact) is stored.

with ExecutionContext() as ctx:
    a = PlayerStat('a').as_string()
    b = PlayerStat('b').as_string()
    dest = PlayerStat('dest').as_string()
    ctx.put(a, 'X' * 20, ignore_warning=True)
    ctx.put(b, 'Y' * 20, ignore_warning=True)
    # Source 28 chars (under 32 limit), but a + b = 40 chars > 32.
    dest.value = '%var.player/a%%var.player/b%'

    def check_rule_fires() -> None:
        # ctx.get_raw bypasses substitution and returns the literal source.
        raw = ctx.get_raw(dest)
        assert raw == '%var.player/a%%var.player/b%', raw

    ctx.assert_all(check_rule_fires)


# --- ExecutionContext: runtime rule does NOT fire when result fits ---

with ExecutionContext() as ctx:
    a = PlayerStat('a').as_string()
    b = PlayerStat('b').as_string()
    dest = PlayerStat('dest').as_string()
    ctx.put(a, 'X' * 5, ignore_warning=True)
    ctx.put(b, 'Y' * 5, ignore_warning=True)
    # Substituted = 10 chars, well under 32, so the substituted value is stored.
    dest.value = '%var.player/a%%var.player/b%'

    def check_substituted() -> None:
        raw = ctx.get_raw(dest)
        assert raw == 'XXXXXYYYYY', raw

    ctx.assert_all(check_substituted)


# --- The chunked emission for a long template results in <= 32 chars per line ---
#
# Use a template that requires >1 chunk. Verify HTSL output, then verify the
# simulator reaches the same final value as a direct (short) set would.

with Container() as container:
    s = PlayerStat('s').as_string()
    # 3 placeholders + literals; with stat self-ref of 14 chars (1-char name),
    # continuation budget is 18 chars. Forces chunking.
    value = '%var.player/p%%var.player/q%%var.player/r%abcdefg'
    assert len(value) > SET_STRING_MAX_LENGTH
    set_string(s, value)

htsl = container.into_htsl()
chunks = htsl.split('\n')
assert len(chunks) >= 2, htsl
for line in chunks:
    src = line.split('"', 2)[1]
    assert len(src) <= SET_STRING_MAX_LENGTH, (len(src), src)


# Number of emitted BinaryExpressions for a chunked set_string equals
# number of chunks (each chunk is one Set BinaryExpression, no others).
with Container() as container:
    s = PlayerStat('s').as_string()
    value = '%var.player/p%%var.player/q%%var.player/r%abcdefg'
    set_string(s, value)

counts = container.expression_counts(nested=True)
assert BinaryExpression in counts, counts
# The exact number depends on how greedily we pack; assert the lines of HTSL
# match the BE count.
n_lines = len(container.into_htsl().split('\n'))
assert counts[BinaryExpression] == n_lines, (counts, n_lines)
