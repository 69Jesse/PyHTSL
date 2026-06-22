import re
from typing import Self, final

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerBlockYPlaceholder',
    'PlayerBlockY',
)


@final
class PlayerBlockYPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.y%')),
    pattern_factory=lambda _: PlayerBlockY,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.block.y%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerBlockY = PlayerBlockYPlaceholder()
