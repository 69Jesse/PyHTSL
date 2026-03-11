from typing import Self, final

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType

__all__ = ('display_action_bar',)


@final
class DisplayActionBarExpression(Expression):
    text: Checkable | HousingType

    def __init__(self, text: Checkable | HousingType) -> None:
        self.text = text

    def into_htsl(self) -> str:
        return f'actionBar "{self.inline(self.text)}"'

    def cloned(self) -> Self:
        return self.__class__(text=self.cloned_or_same(self.text))

    def equals(self, other: object) -> bool:
        if not isinstance(other, DisplayActionBarExpression):
            return False
        return self.equals_or_eq(self.text, other.text)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.text}>'


def display_action_bar(
    text: Checkable | HousingType | None = None,
) -> None:
    resolved: Checkable | HousingType = text if text is not None else '&r'  # type: ignore
    DisplayActionBarExpression(text=resolved).write()
