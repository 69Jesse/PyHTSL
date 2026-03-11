from ..expression.condition.named_condition import NamedCondition

__all__ = ('PlayerFlying',)


class PlayerFlyingCondition(NamedCondition):
    def __init__(self) -> None:
        super().__init__('isFlying')


PlayerFlying = PlayerFlyingCondition()
