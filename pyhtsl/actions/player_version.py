import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerVersion',)


class PlayerVersionPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.version%')),
    pattern_factory=lambda _: PlayerVersion,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.version%',
            comparison_left_side='placeholder "%player.version%"',
            comparison_right_side='%player.version%',
            in_string='%player.version%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


PlayerVersion = PlayerVersionPlaceholder()
