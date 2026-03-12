from typing import TYPE_CHECKING, Self, final

from ..expression.expression import Expression
from ..types import GOTO_CONTAINER

__all__ = ('goto',)


@final
class GotoExpression(Expression):
    container: GOTO_CONTAINER
    name: str

    def __init__(self, container: GOTO_CONTAINER, name: str) -> None:
        self.container = container
        self.name = name

    def into_htsl(self) -> str:
        return f'goto {self.container} {self.inline_quoted(self.name)}'

    def cloned(self) -> Self:
        return self.__class__(container=self.container, name=self.name)

    def equals(self, other: object) -> bool:
        if not isinstance(other, GotoExpression):
            return False
        return self.container == other.container and self.name == other.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.container} {self.name}>'


def _goto(
    container: GOTO_CONTAINER,
    name: str,
    *,
    add_to_front: bool = False,
) -> None:
    expression = GotoExpression(container=container, name=name)
    if add_to_front:
        from ..container import get_current_container

        expressions = get_current_container().get_expressions_ref_in_context()
        expressions.insert(0, expression.cloned())
    else:
        expression.write()


if TYPE_CHECKING:

    def goto(
        container: GOTO_CONTAINER,
        name: str,
    ) -> None: ...
else:
    goto = _goto
