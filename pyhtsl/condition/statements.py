from ..write import write

from typing import Optional
from types import TracebackType


class IfStatement:
    ...


class ElseStatement:
    __slots__ = ()

    def __enter__(self) -> None:
        write('else {')

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        write('}')


def If(
    condition: IfStatement | Condition,
) -> IfStatement:
    if isinstance(condition, IfStatement):
        return condition
    return IfStatement(condition)
