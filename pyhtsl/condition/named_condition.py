from .base_condition import BaseCondition

from typing import final


__all__ = ('NamedCondition',)


@final
class NamedCondition(BaseCondition):
    name: str

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def create_line(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}>'
