from ..stat.stat import Stat

from typing import final


__all__ = (
    'PlayerStat',
)


@final
class PlayerStat(Stat):
    @staticmethod
    def get_prefix() -> str:
        return 'stat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'player'
