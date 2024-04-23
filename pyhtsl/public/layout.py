
__all__ = (
    'Layout',
)


class Layout:
    name: str
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Layout):
            return NotImplemented
        return self.name == other.name
