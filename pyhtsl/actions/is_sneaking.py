from ..expression.condition.named_condition import NamedCondition

__all__ = (
    'IsSneakingCondition',
    'IsSneaking',
)


class IsSneakingCondition(NamedCondition):
    def __init__(self) -> None:
        super().__init__('isSneaking')


IsSneaking = IsSneakingCondition()
