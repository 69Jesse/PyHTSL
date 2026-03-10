import re
from typing import final

from pyhtsl.expression.housing_type import housing_type_from_string

from .player_stat import _split_parts
from .stat import Stat

__all__ = ('GlobalStat',)


def _global_stat_factory(match: re.Match[str]) -> 'GlobalStat':
    parts = _split_parts(match.group(1))
    name = parts[0] if len(parts) > 0 else ''
    stat = GlobalStat(name)
    if len(parts) > 1:
        stat = stat.with_fallback(housing_type_from_string(parts[1]))
    return stat


@final
class GlobalStat(
    Stat,
    pattern=re.compile(r'%var\.global/([^%]+)%'),
    pattern_factory=_global_stat_factory,
):
    @staticmethod
    def left_side_keyword() -> str:
        return 'globalvar'

    @staticmethod
    def right_side_keyword() -> str:
        return 'global'

    def cloned_raw(self) -> 'GlobalStat':
        return GlobalStat(self.name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name} {self.internal_type.name}>'
