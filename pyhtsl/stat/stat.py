from .value import StatValue
from ..condition import PlaceholderValue

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Any, Optional
if TYPE_CHECKING:
    from ..expression import Expression
    from ..condition import Condition, IfStatement
    from ..writer import LineType
    from typing import Self


__all__ = (
    'Stat',
    'StatParameter',
)


STAT_CACHE: dict[
    type['Stat'],
    dict[tuple[str, Optional[str]], 'Stat'],  # {(name, team or None): Stat}
] = {}


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


class Stat(ABC):
    name: str
    __value: StatValue
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
            self.__value = StatValue(self)

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

    @property
    def value(self) -> StatValue:
        return self.__value

    @value.setter
    def value(self, value: 'StatValue | Expression | Stat | int | PlaceholderValue') -> None:
        if isinstance(value, StatValue):
            value = value.stat
        self.__value.set(value)

    def set(self, value: 'Expression | Stat | int | PlaceholderValue') -> None:
        self.value = value

    def with_value(self, value: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        self.value = value
        return self

    def __iadd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        self.value += other
        return self

    def __add__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return self.value + other

    def __radd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return other + self.value

    def __isub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        self.value -= other
        return self

    def __sub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return self.value - other

    def __rsub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return other - self.value

    def __imul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        self.value *= other
        return self

    def __mul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return self.value * other

    def __rmul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return other * self.value

    def __itruediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        self.value /= other
        return self

    def __truediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return self.value / other

    def __ifloordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        self.value //= other
        return self

    def __floordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return self.value // other

    def __pow__(self, other: int) -> 'Expression | int':
        return self.value ** other

    def __neg__(self) -> 'Expression':
        return -self.value

    def __eq__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> 'Condition':
        return PlaceholderValue.equals(self, other)

    def __ne__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> 'IfStatement':
        return PlaceholderValue.not_equal(self, other)

    def __gt__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> 'Condition':
        return PlaceholderValue.greater_than(self, other)

    def __lt__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> 'Condition':
        return PlaceholderValue.less_than(self, other)

    def __ge__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> 'Condition':
        return PlaceholderValue.greater_than_or_equal(self, other)

    def __le__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> 'Condition':
        return PlaceholderValue.less_than_or_equal(self, other)

    def operational_expression_left_side(self) -> str:
        return repr(self)
