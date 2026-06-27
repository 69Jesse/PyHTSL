from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Self, final

from .actions.function import Function
from .base_object import BaseObject
from .container import ContainerContextManager, ExpressionContext
from .limits import fix_action_limits
from .utils.log import log

if TYPE_CHECKING:
    from .container import Container
    from .execute.context import ExecutionContext
    from .expression.expression import Expression


class Block(BaseObject):
    container: 'Container'
    expressions: list['Expression']
    callback: Callable[[], None] | None
    callback_ran: bool
    _overflow_root_ref: 'Block | None'
    _overflow_counter: int

    def __init__(
        self,
        *,
        expressions: list['Expression'] | None = None,
        callback: Callable[[], None] | None = None,
    ) -> None:
        self.expressions = expressions if expressions is not None else []
        self.callback = callback
        self.callback_ran = False
        self._overflow_root_ref = None
        self._overflow_counter = 1

    def expression_counts(
        self,
        *,
        nested: bool = False,
    ) -> dict[type['Expression'], int]:
        counts: dict[type[Expression], int] = {}
        expressions = self.expressions.copy()
        for expr in expressions:
            counts[type(expr)] = counts.get(type(expr), 0) + 1
            if not nested:
                continue
            for sub_expressions in expr.nested_expressions_refs():
                expressions.extend(sub_expressions)
        return counts

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

    def is_empty(self) -> bool:
        return len(self.expressions) == 0

    def into_htsl(self) -> str:
        # Activate the container's temp reservation for *every* HTSL render path
        # transient temps never reuse a `tmp<n>` a consumer named or a held temp
        # was pinned to. This is the single chokepoint — don't rely on callers.
        from .stats.temporary_stat import reserved_temp_numbers

        reserved = getattr(self.container, '_reserved_temp_numbers', set())
        with reserved_temp_numbers(reserved):
            return '\n'.join(expr.into_htsl() for expr in self.expressions)

    def maybe_run_callback(self) -> None:
        if self.callback is None or self.callback_ran:
            return
        self.callback_ran = True
        with BlockContextManager(self):
            self.callback()

    def fix_action_limits(self, container: 'Container', index: int) -> None:
        root = self._overflow_root_ref or self
        base_name = root.get_name()
        next_counter = self._overflow_counter + 1
        function = Function(
            name=f'{base_name} {next_counter}',
        )
        fixed, rest = fix_action_limits(
            self.expressions,
            nesting_possible=True,
            function_if_exceeds=function,
            always_in_conditional=False,
        )
        self.expressions = fixed
        if not rest:
            return
        from .importable import FunctionImportable

        new_block = FunctionBlock(
            function=function,
            expressions=rest,
        )
        new_block._overflow_root_ref = root
        new_block._overflow_counter = next_counter
        container.add_block(new_block, index=index + 1)
        overflow_importable = FunctionImportable(new_block, name=function.name)
        root_function = getattr(root, 'function', None)
        if root_function is not None:
            overflow_importable.module = getattr(
                root_function.__htsw_importable__,
                'module',
                None,
            )
        container.register_importable(overflow_importable)
        log(
            f'Created a new function \x1b[38;2;255;0;0m"{function.name}"\x1b[0m to avoid hitting the action limit in block \x1b[38;2;0;255;0m"{self.get_name()}"\x1b[0m',
        )

    def finalize(self, container: 'Container', index: int) -> None:
        self.maybe_run_callback()
        # An overflow block holds a tail that `fix_action_limits` carved off an
        # already-finalized block, so its expressions are finalized too — a
        # second pass is a no-op. Skipping it avoids quadratic finalize work
        # (a big split-up function would otherwise re-finalize each tail).
        if self._overflow_root_ref is None:
            container.finalize_expressions(self.expressions)
        if not self.container.ignore_action_limits:
            self.fix_action_limits(container, index)

    def execute_all_expressions(self, context: 'ExecutionContext') -> None:
        from .execute.signal import ExitSignal, PauseSignal

        self.maybe_run_callback()
        context.finalize_expressions(self.expressions)

        flat: list[Expression] = []
        for expression in self.expressions:
            flat.extend(expression.into_executable_expressions())

        try:
            context.run_expressions(flat)
        except ExitSignal:
            pass
        except PauseSignal as sig:
            context.schedule_continuation(sig.continuation, sig.ticks)

    def execute(self, context: 'ExecutionContext') -> None:
        pass  # Do nothing on purpose, since most of the time this is but a definition


@final
class GlobalBlock(Block):
    def equals_raw(self, other: object) -> bool:
        return isinstance(other, GlobalBlock)

    def cloned_raw(self) -> Self:
        return self.__class__()

    def get_name(self) -> str:
        return 'Rename Me !!!'

    def execute(self, context: 'ExecutionContext') -> None:
        self.execute_all_expressions(context)


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


@final
class NamedBlock(Block):
    """An action list owned by a non-function importable (item/region/menu/npc)."""

    _name: str

    def __init__(
        self,
        name: str,
        *,
        expressions: list['Expression'] | None = None,
        callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(expressions=expressions, callback=callback)
        self._name = name

    def equals_raw(self, other: object) -> bool:
        return isinstance(other, NamedBlock) and other._name == self._name

    def cloned_raw(self) -> Self:
        return self.__class__(self._name)

    def get_name(self) -> str:
        return self._name


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
