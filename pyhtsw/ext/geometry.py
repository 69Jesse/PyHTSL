from collections.abc import Sequence

from pyhtsw.checkable import Checkable
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.expression.housing_type import NumericHousingType
from pyhtsw.placeholders.player import (
    PlayerPositionX,
    PlayerPositionY,
    PlayerPositionZ,
)
from pyhtsw.stats.temporary_stat import TemporaryStat

__all__ = (
    'distance_squared',
    'player_position',
    'within_distance',
)

type Point = Sequence[Checkable | NumericHousingType]


def player_position() -> tuple[Checkable, Checkable, Checkable]:
    return (PlayerPositionX, PlayerPositionY, PlayerPositionZ)


def distance_squared(
    a: Point,
    b: Point,
    *,
    into: TemporaryStat | None = None,
    axis: TemporaryStat | None = None,
) -> TemporaryStat:
    """The squared distance between two points, in one stat.

    Squaring is `t *= t` rather than `t ** 2`, and the result lands in a stat
    rather than staying an expression, so a caller that both tests it and
    stores it does not compute it twice.
    """
    if len(a) != len(b):
        raise ValueError(
            f'distance_squared: {len(a)} and {len(b)} coordinates do not match',
        )
    total = into if into is not None else TemporaryStat().as_double()
    scratch = axis if axis is not None else TemporaryStat().as_double()
    for index, (left, right) in enumerate(zip(a, b, strict=True)):
        scratch.value = left
        scratch.value -= right
        scratch.value *= scratch
        if index == 0:
            total.value = scratch
        else:
            total.value += scratch
    return total


def within_distance(a: Point, b: Point, distance: float) -> Condition:
    return distance_squared(a, b) <= distance * distance
