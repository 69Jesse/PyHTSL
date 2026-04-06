from collections.abc import Callable
from typing import TYPE_CHECKING, Self

from ...utils.log import log
from .execution_expression import ExecutionExpression

if TYPE_CHECKING:
    from ..context import ExecutionContext


__all__ = ('PrintExecutionExpression',)


class PrintExecutionExpression(ExecutionExpression):
    values: tuple[
        object | Callable[[], object] | Callable[['ExecutionContext'], object],
        ...,
    ]
    cast: bool

    def __init__(
        self,
        values: tuple[
            object | Callable[[], object] | Callable[['ExecutionContext'], object],
            ...,
        ],
        *,
        cast: bool = False,
    ) -> None:
        self.values = values
        self.cast = cast

    def cloned(self) -> Self:
        return self.__class__(values=self.values, cast=self.cast)

    def equals(self, other: object) -> bool:
        if not isinstance(other, PrintExecutionExpression):
            return False
        return self.values == other.values and self.cast == other.cast

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(values={self.values!r}, cast={self.cast!r})'

    def flattened_values(self, context: 'ExecutionContext') -> tuple[object, ...]:
        flattened = []
        for value in self.values:
            if callable(value):
                if value.__code__.co_argcount == 0:
                    flattened.append(value())  # pyright: ignore[reportCallIssue]
                elif value.__code__.co_argcount == 1:
                    flattened.append(value(context))  # pyright: ignore[reportCallIssue]
                else:
                    raise ValueError(
                        f'Callable values must take 0 or 1 arguments, got {value.__code__.co_argcount}'
                    )
            else:
                flattened.append(value)
        return tuple(flattened)

    def raw_execute(self, context: 'ExecutionContext') -> None:
        line = ' '.join(map(str, self.flattened_values(context)))
        log(context.get(line, cast=self.cast, output='string'))
