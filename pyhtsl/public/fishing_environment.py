from ..condition.base_condition import BaseCondition

from typing import final, Literal


__all__ = (
    'FishingEnvironment',
)


@final
class FishingEnvironment(BaseCondition):
    environment: str
    def __init__(
        self,
        environment: Literal['water', 'lava'],
    ) -> None:
        self.environment = environment

    def create_line(self) -> str:
        return f'fishingEnv "{self.environment}"'
