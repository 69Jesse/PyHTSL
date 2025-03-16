from ..condition import TinyCondition
from .item import Item

from typing import final


__all__ = (
    'BlockType',
)


@final
class BlockType(TinyCondition):
    block: Item | str
    match_type_only: bool
    def __init__(
        self,
        block: Item | str,
        match_type_only: bool = False,
    ) -> None:
        self.block = block
        self.match_type_only = match_type_only

    def create_line(self) -> str:
        if isinstance(self.block, Item):
            name = self.block.save()
        else:
            name = self.block
        return f'blockType "{name}" {str(self.match_type_only).lower()}'
