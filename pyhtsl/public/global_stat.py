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
