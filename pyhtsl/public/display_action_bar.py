from ..writer import WRITER, LineType
from ..checkable import Checkable
from ..expression.housing_type import HousingType
from ._inside_line import _inside_line


__all__ = (
    'display_action_bar',
)


def display_action_bar(
    text: Checkable | HousingType | None = None,
) -> None:
    WRITER.write(
        f'actionBar "{_inside_line(text or '&r')}"',
        LineType.miscellaneous,
    )
