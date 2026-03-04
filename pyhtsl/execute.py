import os
from collections.abc import Callable
from types import TracebackType
from typing import TYPE_CHECKING, Self

from .container import Container
from .expression.condition.condition import Condition
from .expression.condition.conditional_expression import ConditionalMode
from .expression.expression import Expression

if TYPE_CHECKING:
    from .expression.expression import Expression


__all__ = ('ExecutionContext',)


class ExecutionContext(Container):
    verbose: bool
    expression_callback: Callable[[Expression], None] | None
    started_execution: bool

    def __init__(
        self,
        *,
        verbose: bool = False,
        expression_callback: Callable[[Expression], None] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name or f'ExecutionContext-{os.urandom(4).hex()}')
        self.verbose = verbose
        self.expression_callback = expression_callback
        self.started_execution = False

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        self.started_execution = True
        for expression in self.expressions:
            for expr in expression.into_executable_expressions():
                expr.execute(self)

    def replace_placeholders(self, text: str) -> str:
        # TODO
        return text

    def write_or_execute(self, expression: Expression) -> None:
        if self.started_execution:
            expression.execute(self)
        else:
            self.write_expression(expression)

    def print(self, *lines: str) -> None:
        self.write_or_execute(
            PrintExecutionExpression(
                line=' '.join(lines),
            )
        )

    def assert_all(self, *conditions: Condition, message: object = None) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                list(conditions),
                mode=ConditionalMode.AND,
                message=str(message) if message is not None else None,
            )
        )

    def assert_any(self, *conditions: Condition, message: object = None) -> None:
        self.write_or_execute(
            AssertExecutionExpression(
                list(conditions),
                mode=ConditionalMode.OR,
                message=str(message) if message is not None else None,
            )
        )


class ExecutionExpression(Expression):
    def into_htsl(self) -> str:
        return f'// {self!r}'


class PrintExecutionExpression(ExecutionExpression):
    line: str

    def __init__(self, line: str) -> None:
        self.line = line

    def cloned(self) -> Self:
        return self.__class__(line=self.line)

    def equals(self, other: object) -> bool:
        if not isinstance(other, PrintExecutionExpression):
            return False
        return self.line == other.line

    def __repr__(self) -> str:
        return f'PrintExecutionExpression(line={self.line!r})'

    def raw_execute(self, context: ExecutionContext) -> None:
        print(context.replace_placeholders(self.line))


class AssertExecutionExpression(ExecutionExpression):
    conditions: list[Condition]
    mode: ConditionalMode
    message: str | None

    def __init__(
        self,
        conditions: list[Condition],
        *,
        mode: ConditionalMode,
        message: str | None = None,
    ) -> None:
        self.conditions = conditions
        self.mode = mode
        self.message = message

    def cloned(self) -> Self:
        return self.__class__(
            conditions=[cond.cloned() for cond in self.conditions],
            mode=self.mode,
            message=self.message,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, AssertExecutionExpression):
            return False
        if self.mode != other.mode:
            return False
        if len(self.conditions) != len(other.conditions):
            return False
        return all(
            self.conditions[i].equals(other.conditions[i])
            for i in range(len(self.conditions))
        )

    def __repr__(self) -> str:
        return f'AssertExecutionExpression(conditions={self.conditions!r}, mode={self.mode!r})'

    def raw_execute(self, context: ExecutionContext) -> None:
        if self.mode == ConditionalMode.AND:
            for condition in self.conditions:
                if not condition.execute(context):
                    raise AssertionError(
                        context.replace_placeholders(self.message)
                        if self.message
                        else None
                    )
        elif self.mode == ConditionalMode.OR:
            for condition in self.conditions:
                if condition.execute(context):
                    return
            raise AssertionError(
                context.replace_placeholders(self.message) if self.message else None
            )
