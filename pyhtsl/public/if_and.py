from ..condition.base_condition import BaseCondition
from ..condition.conditional_statements import ConditionalMode, IfStatement


__all__ = (
    'IfAnd',
)


def IfAnd(
    *conditions: 'BaseCondition',
) -> IfStatement:
    return IfStatement(list(conditions), mode=ConditionalMode.AND)
