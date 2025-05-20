from ..checkable import Checkable
from ..expression.housing_type import HousingType
from ..expression.handler import EXPR_HANDLER


__all__ = (
    '_inside_line',
)


def _inside_line(value: Checkable | HousingType) -> str:
    EXPR_HANDLER.push()
    if isinstance(value, HousingType):
        return str(value)
    return value._in_assignment_right_side()
