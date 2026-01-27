from .stat import Stat


__all__ = ('StatParameter',)


class StatParameter:
    name: str
    cls: type['Stat']

    def __init__(
        self,
        name: str,
        cls: type['Stat'],
    ) -> None:
        self.name = name
        self.cls = cls

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StatParameter):
            return NotImplemented
        return self.name == other.name and self.cls is other.cls
