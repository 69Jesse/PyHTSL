from .writer import WRITER, TemporaryContainerContextManager, ExportContainer
from .expression.handler import LinesType

from types import TracebackType
from typing import Self


class Evaluator:
    all_lines: list[LinesType]
    context: TemporaryContainerContextManager
    container: ExportContainer

    def __init__(self) -> None:
        self.all_lines = []
        self.context = WRITER.temporary_container_context('temp-evaluator', lines_callback=self._lines_callback)
        self.container = self.context.__enter__()

    def _lines_callback(self, lines: LinesType) -> None:
        self.all_lines.append(lines.copy())

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.context.__exit__(exc_type, exc_value, traceback)

    def get_lines(self) -> LinesType:
        lines: LinesType = []
        for line in self.all_lines:
            lines.extend(line)
        return lines

    def get_lines_unflattened(self) -> list[LinesType]:
        return self.all_lines
