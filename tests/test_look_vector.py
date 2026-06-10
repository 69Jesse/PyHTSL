"""approximate_look_vector from pyhtsl.ext: the computed unit vector matches
Minecraft's look formula (x = -sin(yaw)cos(pitch), y = -sin(pitch),
z = cos(yaw)cos(pitch)) within the approximate-trig tolerance, for several
yaw/pitch pairs."""

import math

from pyhtsl import ExecutionContext, PlayerStat, disable_global_export
from pyhtsl.actions.player_position_pitch import PlayerPositionPitch
from pyhtsl.actions.player_position_yaw import PlayerPositionYaw
from pyhtsl.ext import approximate_look_vector

disable_global_export()

TOLERANCE = 0.03


def assert_look_close(yaw: float, pitch: float) -> None:
    with ExecutionContext() as ctx:
        ctx.current_player.put(PlayerPositionYaw, yaw)
        ctx.current_player.put(PlayerPositionPitch, pitch)
        vx = PlayerStat('vx').as_double()
        vy = PlayerStat('vy').as_double()
        vz = PlayerStat('vz').as_double()
        approximate_look_vector(assign_to_x=vx, assign_to_y=vy, assign_to_z=vz)

    yaw_r = math.radians(yaw)
    pitch_r = math.radians(pitch)
    expected_x = -math.sin(yaw_r) * math.cos(pitch_r)
    expected_y = -math.sin(pitch_r)
    expected_z = math.cos(yaw_r) * math.cos(pitch_r)

    got_x = float(ctx.get_raw(vx))
    got_y = float(ctx.get_raw(vy))
    got_z = float(ctx.get_raw(vz))

    assert abs(got_x - expected_x) < TOLERANCE, (yaw, pitch, 'x', got_x, expected_x)
    assert abs(got_y - expected_y) < TOLERANCE, (yaw, pitch, 'y', got_y, expected_y)
    assert abs(got_z - expected_z) < TOLERANCE, (yaw, pitch, 'z', got_z, expected_z)

    # Unit length is preserved (the look vector is normalized).
    magnitude = math.sqrt(got_x**2 + got_y**2 + got_z**2)
    assert abs(magnitude - 1.0) < TOLERANCE, (yaw, pitch, 'mag', magnitude)


# Cardinal directions (pitch 0): yaw 0 → +Z, 90 → -X, -90 → +X, ±180 → -Z.
assert_look_close(0.0, 0.0)
assert_look_close(90.0, 0.0)
assert_look_close(-90.0, 0.0)
assert_look_close(180.0, 0.0)
assert_look_close(-180.0, 0.0)

# Straight up / straight down.
assert_look_close(0.0, 90.0)
assert_look_close(0.0, -90.0)

# A spread of mixed yaw/pitch pairs.
for _yaw in (-135.0, -45.0, 30.0, 60.0, 120.0):
    for _pitch in (-60.0, -20.0, 15.0, 45.0):
        assert_look_close(_yaw, _pitch)


# A non-default yaw/pitch source can be supplied (e.g. stored angles) — here a
# pair of player stats standing in for the executing player's facing.
with ExecutionContext() as ctx:
    stored_yaw = PlayerStat('stored_yaw').as_double()
    stored_pitch = PlayerStat('stored_pitch').as_double()
    ctx.current_player.put(stored_yaw, 90.0)
    ctx.current_player.put(stored_pitch, 0.0)
    vx = PlayerStat('vx').as_double()
    vy = PlayerStat('vy').as_double()
    vz = PlayerStat('vz').as_double()
    approximate_look_vector(
        assign_to_x=vx,
        assign_to_y=vy,
        assign_to_z=vz,
        yaw=stored_yaw,
        pitch=stored_pitch,
    )

# yaw 90 faces -X.
assert abs(float(ctx.get_raw(vx)) - (-1.0)) < TOLERANCE, ctx.get_raw(vx)
assert abs(float(ctx.get_raw(vz)) - 0.0) < TOLERANCE, ctx.get_raw(vz)
