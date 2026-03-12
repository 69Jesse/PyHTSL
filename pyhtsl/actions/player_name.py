import re
from typing import Self, final

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerName',)


@final
class PlayerNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.name%')),
    pattern_factory=lambda _: PlayerName,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return 'Rfind'

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerName = PlayerNamePlaceholder()
