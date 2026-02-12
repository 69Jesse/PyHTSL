from typing import Literal, final

from ..condition.base_condition import BaseCondition

__all__ = ('FishingEnvironment',)


@final
class FishingEnvironment(BaseCondition):
    environment: str

    def __init__(
        self,
        environment: Literal['water', 'lava'],
    ) -> None:
        self.environment = environment

    def into_htsl_raw(self) -> str:
        return f'fishingEnv "{self.environment}"'
