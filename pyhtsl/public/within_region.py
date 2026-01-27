from ..condition.base_condition import BaseCondition
from .region import Region

from typing import final


@final
class WithinRegion(BaseCondition):
    region: Region

    def __init__(
        self,
        region: Region | str,
    ) -> None:
        self.region = region if isinstance(region, Region) else Region(region)

    def create_line(self) -> str:
        return f'inRegion "{self.region.name}"'
