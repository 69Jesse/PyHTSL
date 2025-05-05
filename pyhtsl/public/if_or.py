from ..condition import BaseCondition, ConditionalMode, IfStatement


__all__ = (
    'IfOr',
)


def IfOr(
    *conditions: 'BaseCondition',
) -> IfStatement:
    return IfStatement(list(conditions), mode=ConditionalMode.OR)
