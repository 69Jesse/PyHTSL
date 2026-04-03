from ..expression.condition.named_condition import NamedCondition

__all__ = (
    'PlayerSneakingCondition',
    'PlayerSneaking',
)


class PlayerSneakingCondition(NamedCondition):
    def __init__(self) -> None:
        super().__init__('isSneaking')


PlayerSneaking = PlayerSneakingCondition()
