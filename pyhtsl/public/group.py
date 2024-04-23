
__all__ = (
    'Group',
)


class Group:
    name: str
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Group):
            return NotImplemented
        return self.name == other.name
