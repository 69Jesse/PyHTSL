from ..expression import EXPR_HANDLER
from .stat import Stat
from ..writer import LineType

from typing import final


__all__ = (
    'TemporaryStat',
)


@final
class TemporaryStat(Stat):
    number: int
    def __init__(self) -> None:
        super().__init__(None, set_name=False)  # type: ignore
        self.number = id(self) + 1_000_000

    @property
    def name(self) -> str:
        return f'temp{self.number}'

    @staticmethod
    def get_prefix() -> str:
        return 'stat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'player'

    @property
    def line_type(self) -> LineType:
        return LineType.player_stat_change



EXPR_HANDLER.temporary_stat_cls = TemporaryStat  # type: ignore
