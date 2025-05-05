from .stat import Stat

from typing import final


__all__ = (
    'GlobalStat',
)


@final
class GlobalStat(Stat):
    @staticmethod
    def _left_side_keyword() -> str:
        return 'globalvar'

    @staticmethod
    def _right_side_keyword() -> str:
        return 'global'
