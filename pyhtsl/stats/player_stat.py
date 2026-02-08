from typing import final

from .stat import Stat

__all__ = ('PlayerStat',)


@final
class PlayerStat(Stat):
    @staticmethod
    def _left_side_keyword() -> str:
        return 'var'

    @staticmethod
    def _right_side_keyword() -> str:
        return 'player'

    def cloned_raw(self) -> 'PlayerStat':
        return PlayerStat(self.name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name} {self.internal_type.name}>'
