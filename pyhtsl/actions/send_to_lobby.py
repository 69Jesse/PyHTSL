from typing import Self, final

from ..expression.expression import Expression

__all__ = (
    'SendToLobbyExpression',
    'send_to_lobby',
)


@final
class SendToLobbyExpression(Expression):
    lobby: str

    def __init__(self, lobby: str) -> None:
        self.lobby = lobby

    def into_htsl(self) -> str:
        return f'lobby {self.inline_quoted(self.lobby)}'

    def cloned(self) -> Self:
        return self.__class__(lobby=self.lobby)

    def equals(self, other: object) -> bool:
        if not isinstance(other, SendToLobbyExpression):
            return False
        return self.lobby == other.lobby

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.lobby}>'


def send_to_lobby(lobby: str) -> None:
    SendToLobbyExpression(lobby=lobby).write()
