import re

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('ServerShortName',)


class ServerShortNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%server.shortname%')),
    pattern_factory=lambda _: ServerShortName,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%server.shortname%',
            comparison_left_side='placeholder "%server.shortname%"',
            comparison_right_side='%server.shortname%',
            in_string='%server.shortname%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


ServerShortName = ServerShortNamePlaceholder()
