import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('GroupName',)


class GroupNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.name%')),
    pattern_factory=lambda _: GroupName,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.group.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


GroupName = GroupNamePlaceholder()
