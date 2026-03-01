from pyhtsl.actions.conditional.context_manager import (
    ElseContextManager,
    IfContextManager,
)

from ...expression.condition.condition import Condition
from ...expression.condition.conditional_expression import (
    ConditionalMode,
)

__all__ = (
    'IfAnd',
    'IfOr',
)


def IfAnd(*conditions: Condition) -> IfContextManager:
    return IfContextManager(list(conditions), mode=ConditionalMode.AND)


def IfOr(
    *conditions: Condition,
    and_if_or_does_nothing: bool = True,
) -> IfContextManager:
    return IfContextManager(
        list(conditions),
        mode=ConditionalMode.OR
        if len(conditions) > 1 or not and_if_or_does_nothing
        else ConditionalMode.AND,
    )


Else: ElseContextManager = ElseContextManager()
