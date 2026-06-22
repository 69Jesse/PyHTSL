import re
from typing import Self, final

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderEditable

__all__ = (
    'PlayerHungerPlaceholder',
    'PlayerHunger',
)


@final
class PlayerHungerPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.hunger%')),
    pattern_factory=lambda _: PlayerHunger,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_lhs='hunger',
            as_string='%player.hunger%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerHunger = PlayerHungerPlaceholder()
