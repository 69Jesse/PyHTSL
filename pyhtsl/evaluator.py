from .writer import WRITER, TemporaryContainerContextManager, ExportContainer
from .expression.expression import Expression
from .expression.binary_expression import BinaryExpression

from types import TracebackType  # type: ignore
from typing import Self


class Evaluator:
    all_expressions: list[list[Expression]]
    context: TemporaryContainerContextManager
    container: ExportContainer

    def __init__(self) -> None:
        self.all_expressions = []
        self.context = WRITER.temporary_container_context('temp-evaluator', lines_callback=self._expressions_callback)
        self.container = self.context.__enter__()

    def _expressions_callback(self, expressions: list[Expression]) -> None:
        self.all_expressions.append(expressions.copy())

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.context.__exit__(exc_type, exc_value, traceback)

    def flattened_expressions(self) -> list[Expression]:
        return [expr for sublist in self.all_expressions for expr in sublist]

    def get_expressions(self) -> list[BinaryExpression]:
        return list(filter(lambda e: isinstance(e, BinaryExpression), self.flattened_expressions()))  # type: ignore
