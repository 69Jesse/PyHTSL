from .checkable import Checkable
from .expression.housing_type import HousingType
from .editable import Editable

from typing import final


__all__ = (
    'PlaceholderCheckable',
    'PlaceholderEditable',
)


@final
class PlaceholderCheckable(Checkable):
    right_side: str
    string: str
    def __init__(
        self,
        right_side: str,
        string: str | None = None,
    ) -> None:
        self.right_side = right_side
        self.string = string if string is not None else right_side

    def _left_side_keyword(self) -> str:
        raise RuntimeError('Should not be used')

    def _as_left_side(self) -> str:
        raise RuntimeError('Should not be used')

    def _right_side_keyword(self) -> str:
        raise RuntimeError('Should not be used')

    def _as_right_side(self) -> str:
        return self.right_side

    def _as_string(self) -> str:
        return self.string

    def _equals(self, other: Checkable | HousingType) -> bool:
        return self is other


@final
class PlaceholderEditable(Editable):
    left_side: str
    right_side: str
    string: str
    def __init__(
        self,
        left_side: str,
        right_side: str,
        string: str | None = None,
    ) -> None:
        self.left_side = left_side
        self.right_side = right_side
        self.string = string if string is not None else left_side

    def _left_side_keyword(self) -> str:
        raise RuntimeError('Should not be used')

    def _as_left_side(self) -> str:
        return self.left_side

    def _right_side_keyword(self) -> str:
        raise RuntimeError('Should not be used')

    def _as_right_side(self) -> str:
        return self.right_side

    def _as_string(self) -> str:
        return self.string

    def _equals(self, other: Checkable | HousingType) -> bool:
        return self is other
