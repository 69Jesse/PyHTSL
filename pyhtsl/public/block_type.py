from ..condition import TinyCondition

from typing import final


__all__ = (
    'BlockType',
)


@final
class BlockType(TinyCondition):
    block_name: str
    match_type_only: bool
    def __init__(
        self,
        block_name: str,
        match_type_only: bool = False,
    ) -> None:
        self.block_name = block_name
        self.match_type_only = match_type_only

    def create_line(self) -> str:
        return f'blockType "{self.block_name}" {str(self.match_type_only).lower()}'
