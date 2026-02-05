from .base_condition import BaseCondition

from typing import Self, final


__all__ = ('NamedCondition',)


@final
class NamedCondition(BaseCondition):
    name: str

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def into_htsl_raw(self) -> str:
        return self.name

    def cloned(self) -> Self:
        return self.__class__(
            name=self.name,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, NamedCondition):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}>'
