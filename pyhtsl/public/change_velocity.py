from ..writer import WRITER, LineType
from ..stats.base_stat import BaseStat


__all__ = (
    'change_velocity',
)


def change_velocity(
    x: BaseStat | int,
    y: BaseStat | int,
    z: BaseStat | int,
) -> None:
    WRITER.write(
        f'changeVelocity {x} {y} {z}',
        LineType.miscellaneous,
    )
