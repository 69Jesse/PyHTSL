from ..expression.condition.named_condition import NamedCondition

__all__ = ('IsFlying',)


class IsFlyingCondition(NamedCondition):
	def __init__(self) -> None:
		super().__init__('isFlying')


IsFlying = IsFlyingCondition()
