from ..team import Team
from .value import StatValue
from ..expression import EXPR_HANDLER

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, final, Optional, Any
if TYPE_CHECKING:
    from ..expression import Expression
    from typing import Self


__all__ = (
    'Stat',
    'PlayerStat',
    'GlobalStat',
    'TeamStat',
    'TemporaryStat',
)


class Stat(ABC):
    name: str
    __value: StatValue
    def __init__(self, name: str) -> None:
        self.name = name
        self.__value = StatValue(self)

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

    def __eq__(self, other: Any) -> bool:
        return id(self) == id(other)

    @property
    def value(self) -> StatValue:
        return self.__value

    @value.setter
    def value(self, value: 'StatValue | Expression | Stat | int') -> None:
        if isinstance(value, StatValue):
            assert value is self.__value, 'Cannot set value to another StatValue instance'
            return
        self.__value.set(value)

    def __iadd__(self, other: 'Expression | Stat | int') -> 'Self':
        self.value += other
        return self

    def __add__(self, other: 'Expression | Stat | int') -> 'Expression':
        return self.value + other

    def __isub__(self, other: 'Expression | Stat | int') -> 'Self':
        self.value -= other
        return self

    def __sub__(self, other: 'Expression | Stat | int') -> 'Expression':
        return self.value - other

    def __imul__(self, other: 'Expression | Stat | int') -> 'Self':
        self.value *= other
        return self

    def __mul__(self, other: 'Expression | Stat | int') -> 'Expression':
        return self.value * other

    def __itruediv__(self, other: 'Expression | Stat | int') -> 'Self':
        self.value /= other
        return self

    def __truediv__(self, other: 'Expression | Stat | int') -> 'Expression':
        return self.value / other

    def __ifloordiv__(self, other: 'Expression | Stat | int') -> 'Self':
        self.value //= other
        return self

    def __floordiv__(self, other: 'Expression | Stat | int') -> 'Expression':
        return self.value // other

    def __neg__(self) -> 'Expression':
        return -self.value


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


@final
class TemporaryStat(Stat):
    name: Optional[str]
    number: int
    def __init__(
        self,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name)  # type: ignore
        self.number = -1

    @staticmethod
    def get_prefix() -> str:
        return 'stat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'player'


EXPR_HANDLER.temporary_stat_cls = TemporaryStat  # type: ignore
