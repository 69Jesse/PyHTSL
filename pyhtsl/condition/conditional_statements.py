from ..writer import WRITER, LineType
from ..expression.handler import EXPR_HANDLER

from enum import Enum

from typing import TYPE_CHECKING
from types import TracebackType  # pyright: ignore[reportShadowedImports]

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
        conditions: list['BaseCondition'],
        mode: ConditionalMode = ConditionalMode.AND,
    ) -> None:
        self.conditions = conditions if isinstance(conditions, list) else [conditions]
        self.mode = mode

    def _enter_line(self) -> tuple[str, LineType]:
        return (
            (
                f'if {self.mode.name.lower()} ('
                + ', '.join(map(str, self.conditions))
                + ') {'
            ),
            self.mode.value,
        )

    def __enter__(self) -> None:
        EXPR_HANDLER.push()
        WRITER.write(*self._enter_line())
        WRITER.begin_indent()

    def _exit_line(self) -> tuple[str, LineType]:
        return (
            '}',
            LineType.if_exit,
        )

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        WRITER.end_indent()
        WRITER.write(*self._exit_line())

    def __repr__(self) -> str:
        return f'If<{f' {self.mode.name} '.join(map(repr, self.conditions))}>'


class ElseStatement:
    __slots__ = ()

    def __enter__(self) -> None:
        WRITER.write(
            'else {',
            LineType.else_enter,
            append_to_previous_line=True,
        )
        WRITER.begin_indent()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        WRITER.end_indent()
        WRITER.write(
            '}',
            LineType.else_exit,
        )

    def __repr__(self) -> str:
        return 'Else'
