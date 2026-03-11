from ..expression.condition.named_condition import NamedCondition

__all__ = ('CanPVP',)


class CanPVPCondition(NamedCondition):
	def __init__(self) -> None:
		super().__init__('canPvp')


CanPVP = CanPVPCondition()
