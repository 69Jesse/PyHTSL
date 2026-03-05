import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('ServerName',)


class ServerNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%server.name%')),
    pattern_factory=lambda _: ServerName,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%server.name%',
            comparison_left_side='placeholder "%server.name%"',
            comparison_right_side='%server.name%',
            in_string='%server.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


ServerName = ServerNamePlaceholder()
