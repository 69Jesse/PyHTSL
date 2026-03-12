import re
from typing import Self, final

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('TeamColor',)


@final
class TeamColorPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.team.color%')),
    pattern_factory=lambda _: TeamColor,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.team.color%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''

    def cloned_raw(self) -> Self:
        return self.__class__()


TeamColor = TeamColorPlaceholder()
