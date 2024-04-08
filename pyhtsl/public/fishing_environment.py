from ..condition import TinyCondition

from typing import final, Literal


__all__ = (
    'FishingEnvironment',
)


@final
class FishingEnvironment(TinyCondition):
    environment: str
    def __init__(
        self,
        environment: Literal['water', 'lava'],
    ) -> None:
        self.environment = environment

    def __str__(self) -> str:
        return f'fishingEnv "{self.environment}"'
