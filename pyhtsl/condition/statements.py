from ..write import write

from enum import Enum

from typing import Optional, TYPE_CHECKING
from types import TracebackType
if TYPE_CHECKING:
    from .condition import Condition


__all__ = (
    'ConditionalMode',
    'IfStatement',
    'ElseStatement',
)


class ConditionalMode(Enum):
    AND = 'and'
    OR = 'or'


class IfStatement:
    conditions: list['Condition']
    mode: ConditionalMode
    def __init__(
        self,
        condition: 'Condition | list[Condition]',
        mode: ConditionalMode = ConditionalMode.AND,
    ) -> None:
        self.conditions = condition if isinstance(condition, list) else [condition]
        self.mode = mode

    @staticmethod
    def get_new_conditions(
        left: 'Condition | IfStatement',
        right: 'Condition | IfStatement',
    ) -> list['Condition']:
        left_is_if, right_is_if = isinstance(left, IfStatement), isinstance(right, IfStatement)
        if left_is_if and right_is_if:
            return left.conditions + right.conditions  # type: ignore
        if left_is_if:
            return left.conditions + [right]  # type: ignore
        if right_is_if:
            return [left] + right.conditions  # type: ignore
        return [left, right]  # type: ignore

    def __enter__(self) -> None:
        write(f'if {self.mode.value} (' + ', '.join(map(str, self.conditions)) + ') {')

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        write('}')


class ElseStatement:
    __slots__ = ()

    def __enter__(self) -> None:
        write('else {', append_to_previous_line=True)

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        write('}')
