from ..writer import WRITER, LineType
from ..checkable import Checkable
from ..expression.housing_type import NumericHousingType
from ._inside_line import _inside_line


__all__ = ('change_velocity',)


def change_velocity(
    x: Checkable | NumericHousingType,
    y: Checkable | NumericHousingType,
    z: Checkable | NumericHousingType,
) -> None:
    WRITER.write(
        f'changeVelocity {_inside_line(x)} {_inside_line(y)} {_inside_line(z)}',
        LineType.miscellaneous,
    )
