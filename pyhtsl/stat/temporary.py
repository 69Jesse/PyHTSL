from ..expression import EXPR_HANDLER
from .stat import Stat

from typing import final


__all__ = (
    'TemporaryStat',
)


@final
class TemporaryStat(Stat):
    number: int
    def __init__(self) -> None:
        super().__init__(None, set_name=False)  # type: ignore
        self.number = 0

    @property
    def name(self) -> str:
        return f'temp{self.number}'

    @staticmethod
    def get_prefix() -> str:
        return 'stat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'player'


EXPR_HANDLER.temporary_stat_cls = TemporaryStat  # type: ignore
