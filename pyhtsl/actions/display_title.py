from typing import TYPE_CHECKING, Self, final

from pyhtsl.utils.formatting import formatting_to_ansi
from pyhtsl.utils.log import log

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext

__all__ = (
    'DisplayTitleExpression',
    'display_title',
)


@final
class DisplayTitleExpression(Expression):
    title: Checkable | str
    subtitle: Checkable | str
    fadein: int
    stay: int
    fadeout: int

    def __init__(
        self,
        title: Checkable | str,
        subtitle: Checkable | str,
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
        return f'{self.__class__.__name__}<title={self.title} subtitle={self.subtitle} fadein={self.fadein} stay={self.stay} fadeout={self.fadeout}>'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(
            formatting_to_ansi(
                '&7<display-title>\n'
                f'&7    title: &f{context.get(self.title, cast=False, output="string")}\n'
                f'&7    subtitle: &f{context.get(self.subtitle, cast=False, output="string")}\n'
                f'&7    fadein: &f{self.fadein}\n'
                f'&7    stay: &f{self.stay}\n'
                f'&7    fadeout: &f{self.fadeout}'
            )
        )


def display_title(
    title: Checkable | str | None = None,
    subtitle: Checkable | str | None = None,
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
