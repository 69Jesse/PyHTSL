from typing import TYPE_CHECKING, Self, final

from pyhtsw.utils.formatting import formatting_to_ansi
from pyhtsw.utils.log import log

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext

__all__ = (
    'DisplayActionBarExpression',
    'display_action_bar',
)


@final
class DisplayActionBarExpression(Expression):
    text: Checkable | str

    def __init__(self, text: Checkable | str) -> None:
        self.text = text

    def into_htsl(self) -> str:
        return f'actionBar {self.inline_quoted(self.text)}'

    def cloned(self) -> Self:
        return self.__class__(text=self.cloned_or_same(self.text))

    def equals(self, other: object) -> bool:
        if not isinstance(other, DisplayActionBarExpression):
            return False
        return self.equals_or_eq(self.text, other.text)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.text}>'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(
            formatting_to_ansi(
                '&7<display-action-bar>\n'
                f'&7    text: &f{context.get(self.text, cast=False, output="string")}',
            ),
        )


def display_action_bar(
    text: Checkable | str | None = None,
) -> None:
    resolved: Checkable | HousingType = text if text is not None else '&r'
    DisplayActionBarExpression(text=resolved).write()
