import re
from typing import Self, final

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('GroupTag',)


@final
class GroupTagPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.tag%')),
    pattern_factory=lambda _: GroupTag,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.group.tag%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''

    def cloned_raw(self) -> Self:
        return self.__class__()


GroupTag = GroupTagPlaceholder()
