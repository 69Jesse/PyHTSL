from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, ClassVar, final

from .player_stat import PlayerStat
from .stat import Stat

if TYPE_CHECKING:
    from ..expression.expression import Expression

__all__ = (
    'TemporaryStat',
    'reserved_temp_numbers',
    'currently_reserved_temp_numbers',
)


_RESERVED_NUMBER_STACK: list[set[int]] = []


@contextmanager
def reserved_temp_numbers(numbers: set[int]) -> Generator[None]:
    _RESERVED_NUMBER_STACK.append(numbers)
    try:
        yield
    finally:
        _RESERVED_NUMBER_STACK.pop()


def currently_reserved_temp_numbers() -> set[int]:
    return _RESERVED_NUMBER_STACK[-1] if _RESERVED_NUMBER_STACK else set()


class Number:
    counter: ClassVar[int] = 1_000_000

    @staticmethod
    def new(*, persistent: bool) -> 'Number':
        Number.counter += 1
        return Number(Number.counter, persistent=persistent)

    value: int
    finalized: bool
    persistent: bool

    def __init__(self, value: int, *, persistent: bool) -> None:
        self.value = value
        self.finalized = False
        self.persistent = persistent


@final
class TemporaryStat(Stat):
    name_prefix: ClassVar[str] = 'tmp'

    _number: Number

    def __init__(self) -> None:
        super().__init__('', auto_unset=False)
        self._number = Number.new(persistent=True)

    @classmethod
    def transient(cls) -> 'TemporaryStat':
        stat = cls()
        stat._number.persistent = False
        return stat

    def into_player_stat(self) -> PlayerStat:
        return PlayerStat(self.name, internal_type=self.internal_type)

    def into_hashable(self) -> tuple[object, ...]:
        return self.into_player_stat().into_hashable()

    def resolved_inside_string(self, include_fallback_value: bool = True) -> str:
        return Stat.into_inside_string(self, include_fallback_value)

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        if self._number.finalized:
            return self.resolved_inside_string(include_fallback_value)
        from ..deferred import register_deferred

        return register_deferred(self, include_fallback_value)

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        return self.format_with_internal_type(
            self.resolved_inside_string(),
            include_internal_type=include_internal_type,
        )

    def materialize(self) -> 'tuple[list[Expression], TemporaryStat]':
        return [], self

    @property
    def number(self) -> int:
        return self._number.value

    @number.setter
    def number(self, value: int) -> None:
        self._number.value = value

    @property
    def name(self) -> str:
        return f'{self.name_prefix}{self.number}'

    @name.setter
    def name(self, value: str) -> None:
        pass  # ignore on purpose

    @staticmethod
    def extract_number_from_name(name: str) -> int | None:
        if name.startswith(TemporaryStat.name_prefix):
            try:
                return int(name.removeprefix(TemporaryStat.name_prefix))
            except (ValueError, TypeError):
                pass
        return None

    @staticmethod
    def left_side_keyword() -> str:
        return PlayerStat.left_side_keyword()

    @staticmethod
    def right_side_keyword() -> str:
        return PlayerStat.right_side_keyword()

    def is_execution_player_scoped(self) -> bool:
        return True

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, TemporaryStat):
            return False
        return self.number == other.number

    def cloned_raw(self) -> 'TemporaryStat':
        stat = TemporaryStat()
        stat._number = self._number
        return stat

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.number} {self.internal_type.name}>'
