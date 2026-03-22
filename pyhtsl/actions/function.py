from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyhtsl.block import FunctionBlock

__all__ = ('Function',)


class Function:
    name: str
    block: 'FunctionBlock | None'

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

    def full_rerun(self) -> None:
        from .create_function import create_function

        def run() -> None:
            assert self.block is not None
            for expr in self.block.expressions:
                expr.write()

        create_function(name=self.name, force_create=True)(run)
