from typing import Self, final

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType

__all__ = (
    'DisplayTitleExpression',
    'display_title',
)


@final
class DisplayTitleExpression(Expression):
    title: Checkable | HousingType
    subtitle: Checkable | HousingType
    fadein: int
    stay: int
    fadeout: int

    def __init__(
        self,
        title: Checkable | HousingType,
        subtitle: Checkable | HousingType,
        fadein: int = 1,
        stay: int = 5,
        fadeout: int = 1,
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.fadein = fadein
        self.stay = stay
        self.fadeout = fadeout

    def into_htsl(self) -> str:
        return (
            f'title {self.inline_quoted(self.title)} {self.inline_quoted(self.subtitle)}'
            f' {self.inline(self.fadein)} {self.inline(self.stay)} {self.inline(self.fadeout)}'
        )

    def cloned(self) -> Self:
        return self.__class__(
            title=self.cloned_or_same(self.title),
            subtitle=self.cloned_or_same(self.subtitle),
            fadein=self.fadein,
            stay=self.stay,
            fadeout=self.fadeout,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, DisplayTitleExpression):
            return False
        return (
            self.equals_or_eq(self.title, other.title)
            and self.equals_or_eq(self.subtitle, other.subtitle)
            and self.fadein == other.fadein
            and self.stay == other.stay
            and self.fadeout == other.fadeout
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<title={self.title} subtitle={self.subtitle}>'


def display_title(
    title: Checkable | HousingType | None = None,
    subtitle: Checkable | HousingType | None = None,
    fadein: int = 1,
    stay: int = 5,
    fadeout: int = 1,
) -> None:
    resolved_title: Checkable | HousingType = title if title is not None else '&r'
    resolved_subtitle: Checkable | HousingType = (
        subtitle if subtitle is not None else '&r'
    )
    DisplayTitleExpression(
        title=resolved_title,
        subtitle=resolved_subtitle,
        fadein=fadein,
        stay=stay,
        fadeout=fadeout,
    ).write()
