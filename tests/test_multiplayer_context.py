"""Multi-player ExecutionContext: per-player vs global scope, and the
for-all-players function trigger (with caster self-exclusion via cooldown)."""

from pyhtsl import (
    ExecutionContext,
    ExecutionPlayer,
    GlobalStat,
    IfAll,
    PlayerStat,
    create_function,
    disable_global_export,
    exit_function,
    trigger_function,
)
from pyhtsl.actions.player_name import PlayerName

disable_global_export()


# A `var` (player stat) is stored per-player; the same key on two players holds
# two independent values.
with ExecutionContext(players=['A', 'B']) as ctx:
    a, b = ctx.players
    x = PlayerStat('x').as_long()
    a.put(x, 10)
    b.put(x, 20)

assert int(a.get_raw(x)) == 10, a.get_raw(x)
assert int(b.get_raw(x)) == 20, b.get_raw(x)


# A `globalvar` is shared: writing it as one player is visible to every player
# and to the context.
with ExecutionContext(players=['A', 'B']) as ctx:
    a, b = ctx.players
    g = GlobalStat('shared').as_long()
    a.put(g, 7)

assert int(b.get_raw(g)) == 7, b.get_raw(g)
assert int(ctx.get_raw(g)) == 7, ctx.get_raw(g)


# Each player's name resolves `%player.name%` to themselves.
with ExecutionContext(players=['Alice', 'Bob']) as ctx:
    alice, bob = ctx.players

assert str(alice.get(PlayerName)) == 'Alice', alice.get(PlayerName)
assert str(bob.get(PlayerName)) == 'Bob', bob.get(PlayerName)


# `players=N` makes N auto-named players; `add_player` appends more.
with ExecutionContext(players=3) as ctx:
    assert len(ctx.players) == 3, len(ctx.players)
    extra = ctx.add_player('late')
    assert ctx.players[-1] is extra
    assert len(ctx.players) == 4, len(ctx.players)


# No players given → exactly one default player, which `ctx.put`/`ctx.get`
# (current_player) route through, preserving single-player behavior.
with ExecutionContext() as ctx:
    assert len(ctx.players) == 1, len(ctx.players)
    x = PlayerStat('x').as_long()
    ctx.put(x, 99)

assert int(ctx.get(x)) == 99, ctx.get(x)


# `trigger_function(..., True)` runs the function once per player; a plain
# `trigger_function(...)` runs it only for the current player.
with ExecutionContext(players=['A', 'B', 'C']) as ctx:
    a, b, c = ctx.players
    ctx.current_player = a
    counter = GlobalStat('counter').as_long()
    touched = PlayerStat('touched').as_long()
    ctx.put(counter, 0, ignore_warning=True)

    @create_function('bump')
    def bump() -> None:
        counter.value += 1
        touched.value = 1

    trigger_function(bump, True)  # once per player → 3 runs

assert int(ctx.get_raw(counter)) == 3, ctx.get_raw(counter)
assert int(a.get_raw(touched)) == 1, a.get_raw(touched)
assert int(b.get_raw(touched)) == 1, b.get_raw(touched)
assert int(c.get_raw(touched)) == 1, c.get_raw(touched)


# A function that fans *itself* out runs "for everyone but the caster": the
# caster's own entry call puts the function on its 4-tick cooldown, so the
# inner `… true` skips them. This is the raycast's core mechanism.
with ExecutionContext(players=['A', 'B', 'C']) as ctx:
    a, b, c = ctx.players
    ctx.current_player = a
    active = GlobalStat('active').as_long()
    visited = PlayerStat('visited').as_long()
    ctx.put(active, 0, ignore_warning=True)

    holder: dict[str, object] = {}

    @create_function('spread')
    def spread() -> None:
        with IfAll(active == 0):
            active.value = 1
            trigger_function(holder['fn'], True)  # type: ignore[arg-type]
            exit_function()
        visited.value = 1

    holder['fn'] = spread
    trigger_function(spread)  # A is the caster / origin

assert int(a.get_raw(visited)) == 0, a.get_raw(visited)  # caster excluded
assert int(b.get_raw(visited)) == 1, b.get_raw(visited)
assert int(c.get_raw(visited)) == 1, c.get_raw(visited)


# Passing pre-built ExecutionPlayer objects works, and `.put` on them is usable
# before any expression is written.
p1 = ExecutionPlayer('p1')
p2 = ExecutionPlayer('p2')
with ExecutionContext(players=[p1, p2]) as ctx:
    score = PlayerStat('score').as_long()
    p1.put(score, 5)
    p2.put(score, 8)

assert int(p1.get_raw(score)) == 5, p1.get_raw(score)
assert int(p2.get_raw(score)) == 8, p2.get_raw(score)
