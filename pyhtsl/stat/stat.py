from ..condition import PlaceholderValue

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Any, Optional
if TYPE_CHECKING:
    from ..expression import Expression
    from ..condition import BaseCondition, IfStatement
    from ..writer import LineType
    from typing import Self


__all__ = (
    'Stat',
)


STAT_CACHE: dict[
    type['Stat'],
    dict[tuple[str, Optional[str]], 'Stat'],  # {(name, team or None): Stat}
] = {}


class Stat(Editable):
    name: str
    __value: Expression
    if TYPE_CHECKING:
        def __init__(self, name: str, /) -> None:
            ...
    else:
        def __init__(
            self,
            name: str,
            /,
            *,
            set_name: bool = True,
        ) -> None:
            if set_name:
                self.name = name
            self.__value = self

    def __new__(
        cls,
        *args: Any,
        **kwargs: Any,
    ) -> 'Self':
        """Caching stats based on its name so I can just compare id() and always have it be correct."""
        if cls is Stat:
            raise TypeError('Cannot instantiate Stat class')

        if len(args) == 0:
            return super(Stat, cls).__new__(cls)

        cached = STAT_CACHE.setdefault(cls, {})
        name = args[0]
        assert isinstance(name, str)

        if len(args) > 1:
            maybe_team = args[1]
            maybe_team = maybe_team if isinstance(maybe_team, str) else str(getattr(maybe_team, 'name')) if hasattr(maybe_team, 'name') else None
        else:
            maybe_team = None

        key = (name, maybe_team)
        if key not in cached:
            cached[key] = super(Stat, cls).__new__(cls)
        return cached[key]  # type: ignore

    @staticmethod
    @abstractmethod
    def get_prefix() -> str:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_placeholder_word() -> str:
        raise NotImplementedError

    def get_placeholder(self) -> str:
        return f'%stat.{self.get_placeholder_word()}/{self.name}%'

    def get_htsl_formatted(self) -> str:
        return f'{self.get_prefix()} "{self.name}"'

    @property
    @abstractmethod
    def line_type(self) -> 'LineType':
        raise NotImplementedError

    def __str__(self) -> str:
        return self.get_placeholder()

    def __repr__(self) -> str:
        return self.get_htsl_formatted()

    def __hash__(self) -> int:
        return hash(id(self))
