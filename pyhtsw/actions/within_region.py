from typing import Self, final

from ..expression.condition.condition import Condition
from .region import Region

__all__ = ('WithinRegion',)


def _region_name(region: 'type[Region] | str') -> str:
    if isinstance(region, str):
        return region
    if isinstance(region, type) and issubclass(region, Region):
        return region.__htsw_name__ or region.__name__
    raise TypeError(f'Expected a Region subclass or str, got {region!r}')


@final
class WithinRegion(Condition):
    name: str

    def __init__(self, region: 'type[Region] | str') -> None:
        self.name = _region_name(region)

    def into_htsl_raw(self) -> str:
        return f'inRegion {self.inline_quoted(self.name)}'

    def cloned_raw(self) -> Self:
        return self.__class__(region=self.name)

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, WithinRegion):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}<region={self.name!r} inverted={self.inverted}>'
        )
