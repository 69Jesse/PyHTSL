# Locations

Several actions take a `Location`. Construct one via the factory classmethods —
the bare `Location` class is **not** a valid value.

```python
from pyhtsw import Location

Location.custom(10, 65, 10)                  # x, y, z
Location.custom(10, 65, 10, pitch=0, yaw=90) # with optional pitch/yaw
Location.house_spawn()
Location.invokers()
Location.current()
```

Used by actions such as `teleport_player`, `drop_item`, `play_sound`,
`set_compass_target`, and `launch_to_target`:

```python
from pyhtsw import teleport_player, Location

teleport_player(Location.house_spawn())
teleport_player(Location.custom(10, 65, 10, yaw=180))
```

Coordinates accept numbers or stat/expression values. See the
[HTSL Actions reference](./htsw/htsl/actions.md) for the underlying semantics.
