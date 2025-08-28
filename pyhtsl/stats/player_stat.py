from ..checkable import Checkable
from ..expression.housing_type import HousingType
from .stat import Stat

from typing import final


__all__ = (
    'PlayerStat',
)


@final
class PlayerStat(Stat):
    @staticmethod
    def _left_side_keyword() -> str:
        return 'var'

    @staticmethod
    def _right_side_keyword() -> str:
        return 'player'

    def _equals(self, other: Checkable | HousingType) -> bool:
        if isinstance(other, PlayerStat):
            return self.name == other.name
        return False

    def _copied(self) -> 'PlayerStat':
        return PlayerStat(self.name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name} {self.internal_type.name}>'
