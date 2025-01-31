from ..writer import WRITER, LineType
from ..stat.stat import Stat


__all__ = (
    'change_velocity',
)


def change_velocity(
    x: Stat | int,
    y: Stat | int,
    z: Stat | int,
) -> None:
    WRITER.write(
        f'changeVelocity {x} {y} {z}',
        LineType.miscellaneous,
    )
