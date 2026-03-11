from typing import Self, final

from ..expression.condition.condition import Condition
from .region import Region


@final
class WithinRegion(Condition):
    region: Region

    def __init__(
        self,
        region: Region | str,
    ) -> None:
        self.region = region if isinstance(region, Region) else Region(region)

    def into_htsl_raw(self) -> str:
        return f'inRegion {self.inline_quoted(self.region.name)}'

    def cloned_raw(self) -> Self:
        return self.__class__(region=self.region.cloned())

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, WithinRegion):
            return False
        return self.region.equals(other.region)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<region={self.region!r} inverted={self.inverted}>'
