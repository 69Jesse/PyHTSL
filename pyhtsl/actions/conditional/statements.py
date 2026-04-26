from pyhtsl.actions.conditional.context_manager import (
    ElseContextManager,
    IfContextManager,
)

from ...expression.condition.condition import Condition
from ...expression.condition.conditional_expression import (
    ConditionalMode,
)

__all__ = (
    'IfAll',
    'IfAny',
)


def IfAll(*conditions: Condition) -> IfContextManager:
    return IfContextManager(list(conditions), mode=ConditionalMode.ALL)


def IfAny(
    *conditions: Condition,
    all_if_no_conditions: bool = True,
) -> IfContextManager:
    return IfContextManager(
        list(conditions),
        mode=ConditionalMode.ANY
        if len(conditions) > 1 or not all_if_no_conditions
        else ConditionalMode.ALL,
    )


Else: ElseContextManager = ElseContextManager()
