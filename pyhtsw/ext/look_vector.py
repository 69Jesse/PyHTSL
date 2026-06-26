"""Compute a Minecraft unit look/direction vector from yaw & pitch."""

from ..actions.player_position_pitch import PlayerPositionPitch
from ..actions.player_position_yaw import PlayerPositionYaw
from ..checkable import Checkable
from ..editable import Editable
from ..stats.temporary_stat import TemporaryStat
from .approximate import approximate_sin_cos

__all__ = ('approximate_look_vector',)


def approximate_look_vector(
    *,
    assign_to_x: Editable,
    assign_to_y: Editable,
    assign_to_z: Editable,
    yaw: Checkable = PlayerPositionYaw,
    pitch: Checkable = PlayerPositionPitch,
) -> None:
    """Write the unit look vector for `yaw`/`pitch` into the three stats.

    Minecraft convention:
        x = -sin(yaw)·cos(pitch),  y = -sin(pitch),  z = cos(yaw)·cos(pitch)

    `yaw`/`pitch` default to the executing player's, and are assumed to be in
    Minecraft's ranges ([-180, 180] and [-90, 90]). `assign_to_*` may be any
    editable stats — global, player, temporary — making this reusable for look
    rays, dash/velocity vectors, knockback directions, and so on.
    """
    approximate_sin_cos(
        yaw,
        assign_to_sin=assign_to_x,
        assign_to_cos=assign_to_z,
        certain_x_in_range=180,
        sin_sign=-1,
    )
    xz_multiplier = TemporaryStat().as_double()
    approximate_sin_cos(
        pitch,
        assign_to_sin=assign_to_y,
        assign_to_cos=xz_multiplier,
        certain_x_in_range=90,
        sin_sign=-1,
    )
    assign_to_x.value *= xz_multiplier
    assign_to_z.value *= xz_multiplier
