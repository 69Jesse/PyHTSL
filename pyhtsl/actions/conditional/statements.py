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


def IfOr(*conditions: Condition) -> IfContextManager:
    return IfContextManager(list(conditions), mode=ConditionalMode.OR)


Else: ElseContextManager = ElseContextManager()
