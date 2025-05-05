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
