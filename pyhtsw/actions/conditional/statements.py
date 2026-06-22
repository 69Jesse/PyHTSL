from typing import Literal

from pyhtsw.actions.conditional.context_manager import (
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


def IfAll(*conditions: Condition | Literal[False]) -> IfContextManager:
    return IfContextManager(
        [c for c in conditions if c is not False],
        mode=ConditionalMode.ALL,
    )


def IfAny(
    *conditions: Condition | Literal[False],
    all_if_no_conditions: bool = True,
) -> IfContextManager:
    filtered = [c for c in conditions if c is not False]
    return IfContextManager(
        filtered,
        mode=ConditionalMode.ANY
        if len(filtered) > 1 or not all_if_no_conditions
        else ConditionalMode.ALL,
    )


Else: ElseContextManager = ElseContextManager()
