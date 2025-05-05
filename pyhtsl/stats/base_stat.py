from abc import abstractmethod

from ..checkable import Checkable
from ..expression.housing_type import HousingType
from ..editable import Editable

from typing import TYPE_CHECKING, Any, Optional, Self


__all__ = (
    'BaseStat',
)


STAT_CACHE: dict[
    type['BaseStat'],
    dict[tuple[str, Optional[str]], 'BaseStat'],  # {(name, team or None): Stat}
] = {}


class BaseStat(Editable):
    name: str
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

    def __new__(
        cls,
        *args: Any,
        **kwargs: Any,
    ) -> 'Self':
        """Caching stats based on its name so I can just compare id() and always have it be correct."""
        if cls is BaseStat:
            raise TypeError('Cannot instantiate Stat class')

        if len(args) == 0:
            return super(BaseStat, cls).__new__(cls)

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
            cached[key] = super(BaseStat, cls).__new__(cls)
        return cached[key]  # type: ignore

    def __hash__(self) -> int:
        return hash(id(self))

    @staticmethod
    @abstractmethod
    def _left_side_keyword() -> str:
        """
        var foo = %var.player/bar%
        ^^^
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _right_side_keyword() -> str:
        """
        var foo = %var.player/bar%
                       ^^^^^^
        """
        raise NotImplementedError

    def _in_assignment_left_side(self) -> str:
        return f'{self._left_side_keyword()} {self.name}'

    def _in_assignment_right_side(self) -> str:
        return f'%var.{self._right_side_keyword()}/{self.name}%'

    def _in_comparison_left_side(self) -> str:
        return self._in_assignment_left_side()

    def _in_comparison_right_side(self) -> str:
        return self._in_assignment_right_side()

    def _as_string(self) -> str:
        return self._in_assignment_right_side()

    def _equals(self, other: Checkable | HousingType) -> bool:
        return self is other
