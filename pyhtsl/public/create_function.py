from ..writer import WRITER
from .goto import goto
from .function import Function

from typing import Callable


__all__ = (
    'create_function',
)


def create_function(name: str) -> Callable[[Callable[[], None]], Function]:
    def decorator(func: Callable[[], None]) -> Function:
        def wrapper() -> None:
            goto(container='function', name=name)
            func()
        WRITER.registered_functions.append(wrapper)
        return Function(name=name)
    return decorator
