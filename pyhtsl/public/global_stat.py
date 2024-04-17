from ..writer import LineType
from ..stat.stat import Stat

from typing import final


__all__ = (
    'GlobalStat',
)


@final
class GlobalStat(Stat):
    @staticmethod
    def get_prefix() -> str:
        return 'globalstat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'global'

    @property
    def line_type(self) -> LineType:
        return LineType.global_stat_change
