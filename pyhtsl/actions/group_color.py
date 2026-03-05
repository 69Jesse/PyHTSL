import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('GroupColor',)


class GroupColorPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.color%')),
    pattern_factory=lambda _: GroupColor,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.group.color%',
            comparison_left_side='placeholder "%player.group.color%"',
            comparison_right_side='%player.group.color%',
            in_string='%player.group.color%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


GroupColor = GroupColorPlaceholder()
