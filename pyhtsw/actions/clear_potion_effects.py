from typing import Self, final

from ..expression.expression import Expression

__all__ = (
    'ClearPotionEffectsExpression',
    'clear_potion_effects',
)


@final
class ClearPotionEffectsExpression(Expression):
    def into_htsl(self) -> str:
        return 'clearEffects'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, ClearPotionEffectsExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def clear_potion_effects() -> None:
    ClearPotionEffectsExpression().write()
