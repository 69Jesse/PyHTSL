from ..writer import WRITER, LineType

from enum import Enum

from typing import Optional, TYPE_CHECKING
from types import TracebackType
if TYPE_CHECKING:
    from .condition import BaseCondition


__all__ = (
    'ConditionalMode',
    'IfStatement',
    'ElseStatement',
)


class ConditionalMode(Enum):
    AND = LineType.if_and_enter
    OR = LineType.if_or_enter


class IfStatement:
    conditions: list['BaseCondition']
    mode: ConditionalMode
    def __init__(
        self,
        condition: 'BaseCondition | list[BaseCondition]',
        mode: ConditionalMode = ConditionalMode.AND,
    ) -> None:
        self.conditions = condition if isinstance(condition, list) else [condition]
        self.mode = mode

    @staticmethod
    def get_new_conditions(
        left: 'BaseCondition | IfStatement',
        right: 'BaseCondition | IfStatement',
    ) -> list['BaseCondition']:
        left_is_if, right_is_if = isinstance(left, IfStatement), isinstance(right, IfStatement)
        if left_is_if and right_is_if:
            return left.conditions + right.conditions  # type: ignore
        if left_is_if:
            return left.conditions + [right]  # type: ignore
        if right_is_if:
            return [left] + right.conditions  # type: ignore
        return [left, right]  # type: ignore

    def __enter__(self) -> None:
        WRITER.write(
            f'if {self.mode.name.lower()} (' + ', '.join(map(str, self.conditions)) + ') {',
            self.mode.value,
        )

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        WRITER.write(
            '}',
            LineType.if_exit,
        )


class ElseStatement:
    __slots__ = ()

    def __enter__(self) -> None:
        WRITER.write(
            'else {',
            LineType.else_enter,
            append_to_previous_line=True,
        )

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        WRITER.write(
            '}',
            LineType.else_exit,
        )
