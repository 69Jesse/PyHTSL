from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Self, final

from .actions.function import Function
from .base_object import BaseObject
from .config import INDENT
from .container import ContainerContextManager, ExpressionContext
from .limits import fix_action_limits

if TYPE_CHECKING:
    from .container import Container
    from .execute.context import ExecutionContext
    from .expression.expression import Expression


class Block(BaseObject):
    expressions: list['Expression']
    callback: Callable[[], None] | None
    callback_ran: bool

    def __init__(
        self,
        *,
        expressions: list['Expression'] | None = None,
        callback: Callable[[], None] | None = None,
    ) -> None:
        self.expressions = expressions if expressions is not None else []
        self.callback = callback
        self.callback_ran = False

    @abstractmethod
    def equals_raw(self, other: object) -> bool:
        raise NotImplementedError

    @final
    def equals(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, Block):
            return False
        if len(self.expressions) != len(other.expressions):
            return False
        for expr1, expr2 in zip(self.expressions, other.expressions, strict=True):
            if not expr1.equals(expr2):
                return False
        return self.equals_raw(other)

    @abstractmethod
    def cloned_raw(self) -> Self:
        raise NotImplementedError

    @final
    def cloned(self) -> Self:
        clone = self.cloned_raw()
        clone.expressions = [expr.cloned() for expr in self.expressions]
        clone.callback = self.callback
        clone.callback_ran = self.callback_ran
        return clone

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(expressions={len(self.expressions)})'

    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def goto_line(self) -> str | None:
        raise NotImplementedError()

    def is_empty(self) -> bool:
        return len(self.expressions) == 0

    def into_htsl(self) -> str:
        lines: list[str] = []
        line = self.goto_line()
        if line is not None:
            lines.append(line)
        lines.extend(expr.into_htsl() for expr in self.expressions)
        if line is not None:
            for i in range(1, len(lines)):
                lines[i] = INDENT + lines[i].replace('\n', '\n' + INDENT)
        return '\n'.join(lines)

    def maybe_run_callback(self) -> None:
        if self.callback is None or self.callback_ran:
            return
        with BlockContextManager(self):
            self.callback()
            self.callback_ran = True

    def fix_action_limits(self, container: 'Container', index: int) -> None:
        function_name = f'{self.get_name()} (line {index + 1})'
        fixed, rest = fix_action_limits(
            self.expressions,
            nesting_possible=True,
            function_name_if_exceeds=function_name,
            always_in_conditional=False,
        )
        self.expressions = fixed
        if rest:
            new_block = FunctionBlock(
                function=Function(
                    name=function_name,
                ),
                expressions=rest,
            )
            container.blocks.insert(index + 1, new_block)

    def finalize(self, container: 'Container', index: int) -> None:
        self.maybe_run_callback()
        container.finalize_expressions(self.expressions)
        self.fix_action_limits(container, index)

    def execute(self, context: 'ExecutionContext') -> None:
        pass


@final
class GlobalBlock(Block):
    def equals_raw(self, other: object) -> bool:
        return isinstance(other, GlobalBlock)

    def cloned_raw(self) -> Self:
        return self.__class__()

    def get_name(self) -> str:
        return 'Rename Me !!!'

    def goto_line(self) -> str | None:
        return None

    def execute(self, context: 'ExecutionContext') -> None:
        for expression in self.expressions:
            for expr in expression.into_executable_expressions():
                expr.execute(context)


@final
class FunctionBlock(Block):
    function: Function

    def __init__(
        self,
        function: Function,
        *,
        expressions: list['Expression'] | None = None,
        callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            expressions=expressions,
            callback=callback,
        )
        self.function = function
        assert self.function.block is None
        self.function.block = self

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, FunctionBlock):
            return False
        return self.function == other.function

    def cloned_raw(self) -> Self:
        return self.__class__(function=self.function)

    def get_name(self) -> str:
        return self.function.name

    def goto_line(self) -> str | None:
        return (
            f'goto {self.inline("function")} {self.inline_quoted(self.function.name)}'
        )


@final
class BlockContextManager(ContainerContextManager):
    block: Block

    def __init__(self, block: Block) -> None:
        self.block = block

    def create_context(self) -> ExpressionContext:
        return ExpressionContext(
            parent_expression=None,
            expressions_ref=self.block.expressions,
            add_expression_to_container=False,
        )
