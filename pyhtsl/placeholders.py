from .checkable import Checkable
from .expression.housing_type import HousingType
from .editable import Editable

from typing import final


__all__ = (
    'PlaceholderCheckable',
    'PlaceholderEditable',
)


@final
class PlaceholderCheckable(Editable):
    assignment_right_side: str
    comparison_left_side: str
    comparison_right_side: str
    inside_of_string: str
    def __init__(
        self,
        *,
        assignment_right_side: str,
        comparison_left_side: str,
        comparison_right_side: str,
        in_string: str,
    ) -> None:
        self.assignment_right_side = assignment_right_side
        self.comparison_left_side = comparison_left_side
        self.comparison_right_side = comparison_right_side
        self.inside_of_string = in_string

    def _in_assignment_left_side(self) -> str:
        raise RuntimeError(f'Cannot use {self.__class__.__name__} as left side of assignment.')

    def _in_assignment_right_side(self) -> str:
        return self.assignment_right_side

    def _in_comparison_left_side(self) -> str:
        return self.comparison_left_side

    def _in_comparison_right_side(self) -> str:
        return self.comparison_right_side

    def _as_string(self) -> str:
        return self.inside_of_string

    def _equals(self, other: Checkable | HousingType) -> bool:
        return self is other

    def copied(self) -> 'PlaceholderCheckable':
        return PlaceholderCheckable(
            assignment_right_side=self.assignment_right_side,
            comparison_left_side=self.comparison_left_side,
            comparison_right_side=self.comparison_right_side,
            in_string=self.inside_of_string,
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.inside_of_string}>'


@final
class PlaceholderEditable(Editable):
    assignment_left_side: str
    assignment_right_side: str
    comparison_left_side: str
    comparison_right_side: str
    inside_of_string: str
    def __init__(
        self,
        *,
        assignment_left_side: str,
        assignment_right_side: str,
        comparison_left_side: str,
        comparison_right_side: str,
        in_string: str,
    ) -> None:
        self.assignment_left_side = assignment_left_side
        self.assignment_right_side = assignment_right_side
        self.comparison_left_side = comparison_left_side
        self.comparison_right_side = comparison_right_side
        self.inside_of_string = in_string

    def _in_assignment_left_side(self) -> str:
        return self.assignment_left_side

    def _in_assignment_right_side(self) -> str:
        return self.assignment_right_side

    def _in_comparison_left_side(self) -> str:
        return self.comparison_left_side

    def _in_comparison_right_side(self) -> str:
        return self.comparison_right_side

    def _as_string(self) -> str:
        return self.inside_of_string

    def _equals(self, other: Checkable | HousingType) -> bool:
        return self is other

    def copied(self) -> 'PlaceholderEditable':
        return PlaceholderEditable(
            assignment_left_side=self.assignment_left_side,
            assignment_right_side=self.assignment_right_side,
            comparison_left_side=self.comparison_left_side,
            comparison_right_side=self.comparison_right_side,
            in_string=self.inside_of_string,
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.inside_of_string}>'


Checkable._import_placeholders(PlaceholderCheckable, PlaceholderEditable)
