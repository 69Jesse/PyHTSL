from typing import final

from ..condition.base_condition import BaseCondition
from .item import Item

__all__ = ('BlockType',)


@final
class BlockType(BaseCondition):
    block: Item | str
    match_type_only: bool

    def __init__(
        self,
        block: Item | str,
        match_type_only: bool = False,
    ) -> None:
        self.block = block
        self.match_type_only = match_type_only

    def into_htsl_raw(self) -> str:
        if isinstance(self.block, Item):
            name = self.block.save()
        else:
            name = self.block
        return f'blockType "{name}" {str(self.match_type_only).lower()}'
