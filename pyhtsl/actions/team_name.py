import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('TeamName',)


class TeamNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.team.name%')),
    pattern_factory=lambda _: TeamName,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.team.name%',
            comparison_left_side='placeholder "%player.team.name%"',
            comparison_right_side='%player.team.name%',
            in_string='%player.team.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


TeamName = TeamNamePlaceholder()
