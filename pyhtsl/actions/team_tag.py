import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('TeamTag',)


class TeamTagPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.team.tag%')),
    pattern_factory=lambda _: TeamTag,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.team.tag%',
            comparison_left_side='placeholder "%player.team.tag%"',
            comparison_right_side='%player.team.tag%',
            in_string='%player.team.tag%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


TeamTag = TeamTagPlaceholder()
