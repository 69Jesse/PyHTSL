from ..condition import BaseCondition, ConditionalMode, IfStatement


__all__ = (
    'IfAnd',
)


def IfAnd(
    *conditions: 'BaseCondition',
) -> IfStatement:
    return IfStatement(list(conditions), mode=ConditionalMode.AND)
