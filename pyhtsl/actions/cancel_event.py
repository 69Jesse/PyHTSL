from typing import Self, final

from ..expression.expression import Expression

__all__ = (
    'CancelEventExpression',
    'cancel_event',
)


@final
class CancelEventExpression(Expression):
    def into_htsl(self) -> str:
        return 'cancelEvent'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, CancelEventExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def cancel_event() -> None:
    CancelEventExpression().write()
