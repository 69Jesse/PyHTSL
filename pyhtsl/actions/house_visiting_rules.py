import re
from typing import Self, final

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('HouseVisitingRules',)


@final
class HouseVisitingRulesPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.visitingrules%')),
    pattern_factory=lambda _: HouseVisitingRules,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%house.visitingrules%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''

    def cloned_raw(self) -> Self:
        return self.__class__()


HouseVisitingRules = HouseVisitingRulesPlaceholder()
