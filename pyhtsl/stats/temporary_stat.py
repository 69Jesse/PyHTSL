from ..expression.handler import ExpressionHandler
from ..expression.housing_type import HousingType
from .player_stat import PlayerStat
from .base_stat import BaseStat
from ..checkable import Checkable

from typing import final


__all__ = (
    'TemporaryStat',
)


@final
class TemporaryStat(BaseStat):
    number: int
    def __init__(self) -> None:
        super().__init__(None, set_name=False)  # type: ignore
        self.number = id(self) + 1_000_000
 
    @property
    def name(self) -> str:
        return f'temp{self.number}'

    @staticmethod
    def _left_side_keyword() -> str:
        return PlayerStat._left_side_keyword()

    @staticmethod
    def _right_side_keyword() -> str:
        return PlayerStat._right_side_keyword()

    def _equals(self, other: Checkable | HousingType) -> bool:
        if isinstance(other, TemporaryStat):
            return self.number == other.number
        return False

    def copied(self) -> 'TemporaryStat':
        copy = TemporaryStat()
        copy.number = self.number
        return copy

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.number}>'


ExpressionHandler._import_temporary_stat(TemporaryStat)
Checkable._import_temporary_stat(TemporaryStat)
