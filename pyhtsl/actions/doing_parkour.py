from ..expression.condition.named_condition import NamedCondition

__all__ = ('DoingParkour',)


class DoingParkourCondition(NamedCondition):
	def __init__(self) -> None:
		super().__init__('doingParkour')


DoingParkour = DoingParkourCondition()
