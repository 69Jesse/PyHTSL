from ..writer import WRITER, LineType

from enum import Enum

from typing import Optional, TYPE_CHECKING
from types import TracebackType
if TYPE_CHECKING:
    from .base_condition import BaseCondition


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
        conditions: 'list[BaseCondition]',
        mode: ConditionalMode = ConditionalMode.AND,
    ) -> None:
        self.conditions = conditions if isinstance(conditions, list) else [conditions]
        self.mode = mode

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
