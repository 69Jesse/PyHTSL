from .team import Team
from .expression import Expression

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final
if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = (
    'Stat',
    'PlayerStat',
    'GlobalStat',
    'TeamStat',
)


class Stat(ABC):
    name: str
    def __init__(self, name: str) -> None:
        self.name = name

    @staticmethod
    @abstractmethod
    def get_prefix() -> str:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_placeholder_word() -> str:
        raise NotImplementedError

    def get_placeholder(self) -> str:
        return f'%stat.{self.get_placeholder_word()}/{self.name}%'

    def get_htsl_formatted(self) -> str:
        return f'{self.get_prefix()} {self.name}'

    def __str__(self) -> str:
        return self.get_placeholder()

    def __repr__(self) -> str:
        return self.get_htsl_formatted()

    def __iadd__(self, other: 'Expression | Stat | int') -> 'Self':
        raise NotImplementedError
        return self

    def __add__(self, other: 'Expression | Stat | int') -> Expression:
        raise NotImplementedError

    def __isub__(self, other: 'Expression | Stat | int') -> 'Self':
        raise NotImplementedError
        return self

    def __sub__(self, other: 'Expression | Stat | int') -> Expression:
        raise NotImplementedError

    @property
    def value(self) -> None:
        raise ValueError('`value` is a write-only property')

    @value.setter
    def value(self, value: 'Expression | Stat | int') -> None:
        raise NotImplementedError

    def __imul__(self, other: 'Expression | Stat | int') -> 'Self':
        raise NotImplementedError
        return self

    def __mul__(self, other: 'Expression | Stat | int') -> Expression:
        raise NotImplementedError

    def __itruediv__(self, other: 'Expression | Stat | int') -> 'Self':
        raise NotImplementedError
        return self

    def __truediv__(self, other: 'Expression | Stat | int') -> Expression:
        raise NotImplementedError

    def __ifloordiv__(self, other: 'Expression | Stat | int') -> 'Self':
        return self.__itruediv__(other)

    def __floordiv__(self, other: 'Expression | Stat | int') -> Expression:
        return self.__truediv__(other)


@final
class PlayerStat(Stat):
    @staticmethod
    def get_prefix() -> str:
        return 'stat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'player'


@final
class GlobalStat(Stat):
    @staticmethod
    def get_prefix() -> str:
        return 'globalstat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'global'


@final
class TeamStat(Stat):
    team: Team
    def __init__(self, name: str, team: Team | str) -> None:
        super().__init__(name)
        self.team = team if isinstance(team, Team) else Team(team)

    @staticmethod
    def get_prefix() -> str:
        return 'teamstat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'team'

    def get_htsl_formatted(self) -> str:
        return f'{super().get_htsl_formatted()} {self.team.name}'
