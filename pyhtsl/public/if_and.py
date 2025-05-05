from ..condition import BaseCondition, ConditionalMode, IfStatement


__all__ = (
    'IfAnd',
)


def IfAnd(
    *conditions: 'BaseCondition | IfStatement',
) -> IfStatement:
    new_conditions: list[BaseCondition] = []
    for condition in conditions:
        if isinstance(condition, IfStatement):
            if condition.mode is not ConditionalMode.AND:
                raise ValueError('IfAnd only accepts IfStatements with mode ConditionalMode.AND')
            new_conditions.extend(condition.conditions)
        else:
            new_conditions.append(condition)
    return IfStatement(new_conditions, mode=ConditionalMode.AND)
