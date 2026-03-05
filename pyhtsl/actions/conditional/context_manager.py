from typing import TYPE_CHECKING, final

from pyhtsl.container import ExpressionContext

from ...container import ContainerContextManager, get_current_container
from ...expression.condition.conditional_expression import (
    ConditionalExpression,
    ConditionalMode,
)

if TYPE_CHECKING:
    from ...expression.condition.condition import Condition


@final
class IfContextManager(ContainerContextManager):
    expression: ConditionalExpression

    def __init__(self, conditions: list['Condition'], mode: ConditionalMode) -> None:
        self.expression = ConditionalExpression(conditions, mode)

    def create_context(self) -> ExpressionContext:
        return ExpressionContext(
            parent_expression=self.expression,
            expressions_ref=self.expression.if_expressions,
        )


@final
class ElseContextManager(ContainerContextManager):
    def create_context(self) -> ExpressionContext:
        expressions = get_current_container().get_expressions_ref_in_context()
        if len(expressions) == 0 or not isinstance(
            expressions[-1],
            ConditionalExpression,
        ):
            raise SyntaxError('else without matching if')

        expression = expressions[-1]
        return ExpressionContext(
            parent_expression=expression,
            expressions_ref=expression.else_expressions,
            add_expression_to_container=False,
        )
