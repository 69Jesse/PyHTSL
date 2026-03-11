from typing import Self, final

from ..expression.condition.condition import Condition
from ..types import FISHING_ENVIRONMENTS

__all__ = ('FishingEnvironment',)


@final
class FishingEnvironment(Condition):
    environment: FISHING_ENVIRONMENTS

    def __init__(
        self,
        environment: FISHING_ENVIRONMENTS,
    ) -> None:
        self.environment = environment

    def into_htsl_raw(self) -> str:
        return f'fishingEnv {self.inline_quoted(self.environment)}'

    def cloned_raw(self) -> Self:
        return self.__class__(environment=self.environment)

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, FishingEnvironment):
            return False
        return self.environment == other.environment

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.environment} inverted={self.inverted}>'
