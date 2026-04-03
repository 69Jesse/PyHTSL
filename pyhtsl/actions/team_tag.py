import re
from typing import Self, final

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'TeamTagPlaceholder',
    'TeamTag',
)


@final
class TeamTagPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.team.tag%')),
    pattern_factory=lambda _: TeamTag,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.team.tag%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''

    def cloned_raw(self) -> Self:
        return self.__class__()


TeamTag = TeamTagPlaceholder()
