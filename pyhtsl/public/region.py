
__all__ = (
    'Region',
)


class Region:
    name: str
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Region):
            return NotImplemented
        return self.name == other.name
