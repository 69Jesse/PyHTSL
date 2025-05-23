from ..expression.handler import ExpressionHandler
from ..expression.housing_type import HousingType
from .player_stat import PlayerStat
from .base_stat import BaseStat
from ..checkable import Checkable
from ..internal_type import InternalType

from typing import final


__all__ = (
    'TemporaryStat',
)


@final
class TemporaryStat(BaseStat):
    number: int
    def __init__(
        self,
        internal_type: InternalType,
    ) -> None:
        super().__init__(None, set_name=False, unset=False)  # type: ignore
        self.internal_type = internal_type
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

    def _copied(self) -> 'TemporaryStat':
        stat = TemporaryStat(self.internal_type)
        stat.number = self.number
        return stat

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.number}>'


ExpressionHandler._import_temporary_stat(TemporaryStat)
Checkable._import_temporary_stat(TemporaryStat)
