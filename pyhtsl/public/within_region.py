from typing import final

from ..condition.base_condition import BaseCondition
from .region import Region


@final
class WithinRegion(BaseCondition):
    region: Region

    def __init__(
        self,
        region: Region | str,
    ) -> None:
        self.region = region if isinstance(region, Region) else Region(region)

    def into_htsl_raw(self) -> str:
        return f'inRegion "{self.region.name}"'
