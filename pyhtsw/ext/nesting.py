from types import TracebackType

from pyhtsw.compiler.container import (
    ExpressionContext,
    get_current_container,
    nesting_allowed,
)
from pyhtsw.compiler.reemission import clear_emission_marks
from pyhtsw.expression.binary_expression import BinaryExpression, BinaryOperator
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.expression.condition.conditional_expression import (
    ConditionalExpression,
    ConditionalMode,
)
from pyhtsw.expression.expression import Expression
from pyhtsw.stats.temporary_stat import TemporaryStat

__all__ = ('Nestable',)


def _conditionals_in(expressions: list[Expression]) -> bool:
    return any(isinstance(e, ConditionalExpression) for e in expressions)


def _subtree(node: ConditionalExpression) -> list[Expression]:
    out: list[Expression] = []
    for branch in (node.if_expressions, node.else_expressions):
        for expression in branch:
            out.append(expression)
            if isinstance(expression, ConditionalExpression):
                out.extend(_subtree(expression))
    return out


def _retest_is_safe(node: ConditionalExpression) -> bool:
    from pyhtsw.compiler.schedule import conditions_read, effects_of

    reads = conditions_read(node.conditions)
    if reads is None:
        return False
    for expression in _subtree(node):
        effects = effects_of(expression)
        if effects.writes is None or effects.control:
            return False
        if effects.writes & reads:
            return False
    return True


def _absorbable(node: ConditionalExpression) -> bool:
    """Whether both of the node's paths are conjunctions Housing can express."""
    if node.mode is ConditionalMode.ALL:
        return len(node.conditions) == 1 or not node.else_expressions
    return len(node.conditions) == 1


class _Flattener:
    def __init__(self) -> None:
        self.out: list[Expression] = []

    def emit(self, path: list[Condition], run: list[Expression]) -> None:
        if not run:
            return
        if not path:
            self.out.extend(run)
            return
        self.out.append(
            ConditionalExpression(
                [condition.cloned() for condition in path],
                ConditionalMode.ALL,
                if_expressions=list(run),
            ),
        )

    def walk(self, expressions: list[Expression], path: list[Condition]) -> None:
        run: list[Expression] = []
        for expression in expressions:
            if not isinstance(expression, ConditionalExpression):
                run.append(expression)
                continue
            self.emit(path, run)
            run = []
            self.node(expression, path)
        self.emit(path, run)

    def node(self, node: ConditionalExpression, path: list[Condition]) -> None:
        if not path and not _conditionals_in(_subtree(node)):
            self.out.append(node)
            return

        if _absorbable(node) and _retest_is_safe(node):
            taken = (
                node.conditions
                if node.mode is ConditionalMode.ALL
                else [node.conditions[0]]
            )
            self.walk(node.if_expressions, [*path, *taken])
            if node.else_expressions:
                missed = [~condition for condition in node.conditions]
                self.walk(node.else_expressions, [*path, *missed])
            return

        flag = TemporaryStat().as_long()
        conjunctive = node.mode is ConditionalMode.ALL
        test = [*path, *node.conditions] if conjunctive else list(node.conditions)
        self.out.append(
            ConditionalExpression(
                [condition.cloned() for condition in test],
                node.mode,
                if_expressions=[BinaryExpression(flag, 1, BinaryOperator.Set)],
                else_expressions=[BinaryExpression(flag, 0, BinaryOperator.Set)],
            ),
        )
        self.walk(node.if_expressions, [*path, flag == 1])
        if node.else_expressions:
            self.walk(node.else_expressions, [*path, flag == 0])


class Nestable:
    """Lets conditionals nest to any depth inside the ``with`` body.

    Housing has no nested conditionals, so each action run is re-emitted at top
    level under its whole path. A path step merges into that guard for free
    when it is a conjunction Housing can express and nothing in the body writes
    what it reads; otherwise the step is materialised into a flag first.
    """

    def __init__(self) -> None:
        self._captured: list[Expression] = []
        self._allowance = nesting_allowed()

    def __enter__(self) -> None:
        container = get_current_container()
        boundary = -1
        for index, context in enumerate(container.contexts):
            if context.parent_expression is None:
                boundary = index
        for context in container.contexts[boundary + 1 :]:
            parent = context.parent_expression
            if parent is not None and not parent.can_be_nested():
                raise SyntaxError(
                    'Nestable() has to be opened at the top level of a block, '
                    'not inside an if/random. Open it first and put the '
                    'conditional inside it.',
                )
        container.add_context(ExpressionContext(None, self._captured))
        self._allowance.__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._allowance.__exit__(exc_type, exc_value, traceback)
        container = get_current_container()
        container.pop_context()
        if exc_type is not None:
            return
        clear_emission_marks(self._captured)
        flattener = _Flattener()
        flattener.walk(self._captured, [])
        for expression in flattener.out:
            container.write_expression(expression)
