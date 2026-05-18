import re
from typing import Self, final

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerPingPlaceholder',
    'PlayerPing',
)


@final
class PlayerPingPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.ping%')),
    pattern_factory=lambda _: PlayerPing,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.ping%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerPing = PlayerPingPlaceholder()
