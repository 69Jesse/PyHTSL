from typing import Callable


__all__ = ('Function',)


class Function[CT: Callable[[], None] | None]:
    name: str
    callback: CT

    def __init__(
        self,
        name: str,
        *,
        callback: CT = None,
    ) -> None:
        self.name = name
        self.callback = callback

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Function):
            return NotImplemented
        return self.name == other.name
