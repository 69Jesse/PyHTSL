from .checkable import Checkable
from .editable import Editable

from typing import final


__all__ = (
    'PlaceholderCheckable',
    'PlaceholderEditable',
)


@final
class PlaceholderCheckable(Checkable):
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

    def into_assignment_left_side(self) -> str:
        raise RuntimeError(
            f'Cannot use {self.__class__.__name__} as left side of assignment.'
        )

    def into_assignment_right_side(self, *, include_internal_type: bool = True) -> str:
        return self._formatted_with_internal_type(
            self.assignment_right_side, include_internal_type=include_internal_type
        )

    def into_comparison_left_side(self) -> str:
        return self.comparison_left_side

    def into_comparison_right_side(self) -> str:
        return self._formatted_with_internal_type(
            self.comparison_right_side, include_internal_type=True
        )

    def into_string(self, include_fallback_value: bool = True) -> str:
        return self.inside_of_string

    def equals_raw(self, other: object) -> bool:
        return self is other

    def cloned_raw(self) -> 'PlaceholderCheckable':
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

    def into_assignment_left_side(self) -> str:
        return self.assignment_left_side

    def into_assignment_right_side(self, *, include_internal_type: bool = True) -> str:
        return self._formatted_with_internal_type(
            self.assignment_right_side, include_internal_type=include_internal_type
        )

    def into_comparison_left_side(self) -> str:
        return self.comparison_left_side

    def into_comparison_right_side(self) -> str:
        return self._formatted_with_internal_type(
            self.comparison_right_side, include_internal_type=True
        )

    def into_string(self, include_fallback_value: bool = True) -> str:
        return self.inside_of_string

    def equals_raw(self, other: object) -> bool:
        return self is other

    def cloned_raw(self) -> 'PlaceholderEditable':
        return PlaceholderEditable(
            assignment_left_side=self.assignment_left_side,
            assignment_right_side=self.assignment_right_side,
            comparison_left_side=self.comparison_left_side,
            comparison_right_side=self.comparison_right_side,
            in_string=self.inside_of_string,
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.inside_of_string}>'
