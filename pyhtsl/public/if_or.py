from ..condition import Condition, ConditionalMode, IfStatement


__all__ = (
    'IfOr',
)


def IfOr(
    *conditions: 'Condition | IfStatement',
) -> IfStatement:
    new_conditions: list[Condition] = []
    for condition in conditions:
        if isinstance(condition, IfStatement):
            if condition.mode is not ConditionalMode.OR:
                raise ValueError('IfOr only accepts IfStatements with mode ConditionalMode.OR')
            new_conditions.extend(condition.conditions)
        else:
            new_conditions.append(condition)
    return IfStatement(new_conditions, mode=ConditionalMode.OR)
