from ..condition.base_condition import BaseCondition
from ..condition.conditional_statements import ConditionalMode, IfStatement


__all__ = ('IfOr',)


def IfOr(
    *conditions: 'BaseCondition',
) -> IfStatement:
    return IfStatement(list(conditions), mode=ConditionalMode.OR)
