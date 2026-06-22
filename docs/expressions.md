# Expressions

PyHTSW models Housing stats and arithmetic as an **expression tree**. Operators
don't compute anything in Python — they record intent that PyHTSW lowers into
HTSL when a block is finalized.

## Stats

```python
from pyhtsw import PlayerStat, GlobalStat, TeamStat, TemporaryStat

coins = PlayerStat('coins')
jackpot = GlobalStat('jackpot')
score = TeamStat('score')
tmp = TemporaryStat('tmp')
```

- `PlayerStat` — per-player.
- `GlobalStat` — house-wide.
- `TeamStat` — per-team.
- `TemporaryStat` — scratch values.

## Arithmetic

Assign through `.value` so augmented assignment works in every context:

```python
coins.value += 100
coins.value = coins * 2 - 5
```

Arithmetic on stats builds a `BinaryExpression` tree; PyHTSW flattens it into a
sequence of HTSL operations on temporaries.

## Conditionals

```python
from pyhtsw import IfAll, IfAny, Else, chat

with IfAll(coins > 100, jackpot == 0):
    chat('rich')
with Else:
    chat('keep saving')

with IfAny(coins > 1000, jackpot > 0):
    chat('lucky')
```

Combine conditions into a single `IfAll(...)` / `IfAny(...)` rather than nesting
them.

## f-string interpolation

Stats and expressions interpolate into action strings:

```python
chat(f'You have {coins} coins.')
chat(f'Double would be {coins * 2}.')
```

PyHTSW emits the computation needed for an interpolated expression before the
statement that uses it.

See the HTSL reference for the underlying semantics:
[Actions](./htsw/htsl/actions.md) and [Conditions](./htsw/htsl/conditions.md).
