from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyhtsw.block import FunctionBlock
    from pyhtsw.importable import FunctionImportable


__all__ = ('Function',)


class Function:
    name: str
    block: 'FunctionBlock | None'
    __htsw_importable__: 'FunctionImportable'

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name
        self.block = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Function):
            return NotImplemented
        return self.name == other.name
