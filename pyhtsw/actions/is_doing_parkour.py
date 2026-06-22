from ..expression.condition.named_condition import NamedCondition

__all__ = (
    'IsDoingParkourCondition',
    'IsDoingParkour',
)


class IsDoingParkourCondition(NamedCondition):
    def __init__(self) -> None:
        super().__init__('doingParkour')


IsDoingParkour = IsDoingParkourCondition()
