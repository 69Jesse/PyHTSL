import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerGamemode',)


class PlayerGamemodePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.gamemode%')),
    pattern_factory=lambda _: PlayerGamemode,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.gamemode%',
            comparison_left_side='placeholder "%player.gamemode%"',
            comparison_right_side='%player.gamemode%',
            in_string='%player.gamemode%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


PlayerGamemode = PlayerGamemodePlaceholder()
