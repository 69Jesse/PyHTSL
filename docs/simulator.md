# Simulator

`ExecutionContext` runs expressions **in Python** instead of emitting HTSL —
useful for testing and debugging logic without importing into a house.

```python
from pyhtsw import ExecutionContext, PlayerStat

coins = PlayerStat('coins')

with ExecutionContext() as ctx:
    ctx.put(coins, 50, ignore_warning=True)
    coins.value += 100

    def check() -> None:
        assert int(ctx.get(coins)) == 150

    ctx.assert_all(check)
```

- `ctx.put(stat, value, ignore_warning=True)` seeds a value.
- `ctx.get(stat)` reads via the HTSL placeholder path; `ctx.get_raw(stat)` reads
  the exact backend value.
- `ctx.assert_all(...)` / `ctx.assert_any(...)` take conditions or plain
  callables that run `assert` checks.
- Everything runs at `__exit__`.

The simulator follows Java arithmetic semantics (64-bit long wraparound,
truncating integer division, etc.) so a simulated program matches what the house
would compute.
