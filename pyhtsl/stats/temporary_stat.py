from ..expression.handler import ExpressionHandler
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


ExpressionHandler._import_temporary_stat(TemporaryStat)
Checkable._import_temporary_stat(TemporaryStat)
