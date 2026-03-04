import os
from collections.abc import Callable
from types import TracebackType
from typing import TYPE_CHECKING

from pyhtsl.expression.expression import Expression

from .container import Container

if TYPE_CHECKING:
    from .expression.expression import Expression


__all__ = ('ExecutionContext',)


class ExecutionContext(Container):
    verbose: bool
    expression_callback: Callable[[Expression], None] | None

    def __init__(
        self,
        *,
        verbose: bool = True,
        expression_callback: Callable[[Expression], None] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name or f'ExecutionContext-{os.urandom(4).hex()}')
        self.expression_callback = expression_callback
        self.verbose = verbose

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        for expression in self.expressions:
            for expr in expression.into_executable_expressions():
                expr.execute(self)
