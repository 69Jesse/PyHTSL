from .player_stat import PlayerStat
from .stat import Stat
from ..internal_type import InternalType

from typing import final


__all__ = ('TemporaryStat',)


class Number:
    value: int

    def __init__(self, value: int) -> None:
        self.value = value


@final
class TemporaryStat(Stat):
    _number: Number

    def __init__(
        self,
        internal_type: InternalType,
    ) -> None:
        super().__init__('', auto_unset=False)
        self.internal_type = internal_type
        self._number = Number(id(self) + 1_000_000)

    @property
    def number(self) -> int:
        return self._number.value

    @number.setter
    def number(self, value: int) -> None:
        self._number.value = value

    @property
    def name(self) -> str:
        return f'temp{self.number}'

    @name.setter
    def name(self, value: str) -> None:
        pass  # ignore on purpose

    @staticmethod
    def _left_side_keyword() -> str:
        return PlayerStat._left_side_keyword()

    @staticmethod
    def _right_side_keyword() -> str:
        return PlayerStat._right_side_keyword()

    def equals_raw(self, other: object) -> bool:
        if isinstance(other, TemporaryStat):
            return self.number == other.number
        return False

    def cloned_raw(self) -> 'TemporaryStat':
        stat = TemporaryStat(self.internal_type)
        stat._number = self._number
        return stat

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.number} {self.internal_type.name}>'
