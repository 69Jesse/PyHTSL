from typing import ClassVar, final

from ..internal_type import InternalType
from .player_stat import PlayerStat
from .stat import Stat

__all__ = ('TemporaryStat',)


class Number:
    value: int

    def __init__(self, value: int) -> None:
        self.value = value


@final
class TemporaryStat(Stat):
    name_prefix: ClassVar[str] = 'tmp'

    _number: Number

    def __init__(
        self,
        internal_type: InternalType,
    ) -> None:
        super().__init__('', auto_unset=False)
        self.internal_type = internal_type
        self._number = Number(id(self) + 1_000_000)

    def into_player_stat(self) -> PlayerStat:
        return PlayerStat(self.name, internal_type=self.internal_type)

    def into_hashable(self) -> tuple[object, ...]:
        return self.into_player_stat().into_hashable()

    @property
    def number(self) -> int:
        return self._number.value

    @number.setter
    def number(self, value: int) -> None:
        self._number.value = value

    @property
    def name(self) -> str:
        return f'{self.name_prefix}{self.number}'

    @name.setter
    def name(self, value: str) -> None:
        pass  # ignore on purpose

    @staticmethod
    def extract_number_from_name(name: str) -> int | None:
        if name.startswith(TemporaryStat.name_prefix):
            try:
                return int(name.removeprefix(TemporaryStat.name_prefix))
            except (ValueError, TypeError):
                pass
        return None

    @staticmethod
    def left_side_keyword() -> str:
        return PlayerStat.left_side_keyword()

    @staticmethod
    def right_side_keyword() -> str:
        return PlayerStat.right_side_keyword()

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, TemporaryStat):
            return False
        return self.number == other.number

    def cloned_raw(self) -> 'TemporaryStat':
        stat = TemporaryStat(self.internal_type)
        stat._number = self._number
        return stat

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.number} {self.internal_type.name}>'
