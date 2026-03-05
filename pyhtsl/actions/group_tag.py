import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('GroupTag',)


class GroupTagPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.tag%')),
    pattern_factory=lambda _: GroupTag,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.group.tag%',
            comparison_left_side='placeholder "%player.group.tag%"',
            comparison_right_side='%player.group.tag%',
            in_string='%player.group.tag%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


GroupTag = GroupTagPlaceholder()
