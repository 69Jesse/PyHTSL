from ..writer import WRITER, LineType
from ..checkable import Checkable
from ..expression.housing_type import HousingType
from ._inside_line import _inside_line


__all__ = ('display_title',)


def display_title(
    title: Checkable | HousingType | None = None,
    subtitle: Checkable | HousingType | None = None,
    fadein: int = 1,
    stay: int = 5,
    fadeout: int = 1,
) -> None:
    WRITER.write(
        f'title "{_inside_line(title or "&r")}" "{_inside_line(subtitle or "&r")}" {fadein} {stay} {fadeout}',
        LineType.display_title,
    )
