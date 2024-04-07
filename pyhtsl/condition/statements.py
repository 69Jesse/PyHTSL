from ..write import write

from enum import Enum

from typing import Optional, TYPE_CHECKING, Iterable
from types import TracebackType
if TYPE_CHECKING:
    from .condition import Condition


__all__ = (
    'If',
    'Else',
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

    @staticmethod
    def logical_and(
        left: 'Condition | IfStatement',
        right: 'Condition | IfStatement',
    ) -> 'IfStatement':
        new_conditions = IfStatement.get_new_conditions(left, right)
        if len(new_conditions) > 2 and (
            isinstance(left, IfStatement) and left.mode is ConditionalMode.OR
            or isinstance(right, IfStatement) and right.mode is ConditionalMode.OR
        ):
            raise ValueError('Cannot mix AND and OR conditions')
        return IfStatement(new_conditions, ConditionalMode.AND)

    @staticmethod
    def logical_or(
        left: 'Condition | IfStatement',
        right: 'Condition | IfStatement',
    ) -> 'IfStatement':
        new_conditions = IfStatement.get_new_conditions(left, right)
        if len(new_conditions) > 2 and (
            isinstance(left, IfStatement) and left.mode is ConditionalMode.AND
            or isinstance(right, IfStatement) and right.mode is ConditionalMode.AND
        ):
            raise ValueError('Cannot mix AND and OR conditions')
        return IfStatement(new_conditions, ConditionalMode.OR)

    def __and__(self, other: 'Condition | IfStatement') -> 'IfStatement':
        return IfStatement.logical_and(self, other)

    def __or__(self, other: 'Condition | IfStatement') -> 'IfStatement':
        return IfStatement.logical_or(self, other)

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
        write('else {')

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        write('}')


def If(
    condition: 'Condition | Iterable[Condition] | IfStatement',
) -> IfStatement:
    if isinstance(condition, IfStatement):
        return condition
    if isinstance(condition, Iterable):
        return IfStatement(list(condition))
    return IfStatement(condition)


Else = ElseStatement()
