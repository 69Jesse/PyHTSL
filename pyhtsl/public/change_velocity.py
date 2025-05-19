from ..writer import WRITER, LineType
from ..checkable import Checkable
from ..expression.housing_type import NumericHousingType


__all__ = (
    'change_velocity',
)


def change_velocity(
    x: Checkable | NumericHousingType,
    y: Checkable | NumericHousingType,
    z: Checkable | NumericHousingType,
) -> None:
    WRITER.write(
        f'changeVelocity {x} {y} {z}',
        LineType.miscellaneous,
    )
