from typing import Self, final

from ..expression.condition.condition import Condition
from .item import Item

__all__ = ('BlockType',)


@final
class BlockType(Condition):
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
        return f'blockType {self.inline_quoted(name)} {self.inline(self.match_type_only)}'

    def cloned_raw(self) -> Self:
        return self.__class__(
            block=self.cloned_or_same(self.block),
            match_type_only=self.match_type_only,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, BlockType):
            return False
        return self.equals_or_eq(self.block, other.block) and self.match_type_only == other.match_type_only

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<block={self.block!r} match_type_only={self.match_type_only} inverted={self.inverted}>'
