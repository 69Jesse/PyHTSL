from typing import Self, final

from ..expression.expression import Expression
from ..types import ALL_POTION_EFFECTS

__all__ = ('apply_potion_effect',)


@final
class ApplyPotionEffectExpression(Expression):
    potion: ALL_POTION_EFFECTS
    duration: int
    level: int
    override_existing_effects: bool
    show_potion_icon: bool

    def __init__(
        self,
        potion: ALL_POTION_EFFECTS,
        duration: int = 60,
        level: int = 1,
        override_existing_effects: bool = False,
        show_potion_icon: bool = False,
    ) -> None:
        self.potion = potion
        self.duration = duration
        self.level = level
        self.override_existing_effects = override_existing_effects
        self.show_potion_icon = show_potion_icon

    def into_htsl(self) -> str:
        return (
            f'applyPotion {self.inline_quoted(self.potion)} {self.inline(self.duration)} {self.inline(self.level)}'
            f' {self.inline(self.override_existing_effects)} {self.inline(self.show_potion_icon)}'
        )

    def cloned(self) -> Self:
        return self.__class__(
            potion=self.potion,
            duration=self.duration,
            level=self.level,
            override_existing_effects=self.override_existing_effects,
            show_potion_icon=self.show_potion_icon,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, ApplyPotionEffectExpression):
            return False
        return (
            self.potion == other.potion
            and self.duration == other.duration
            and self.level == other.level
            and self.override_existing_effects == other.override_existing_effects
            and self.show_potion_icon == other.show_potion_icon
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.potion} duration={self.duration} level={self.level}>'


def apply_potion_effect(
    potion: ALL_POTION_EFFECTS,
    duration: int = 60,
    level: int = 1,
    override_existing_effects: bool = False,
    show_potion_icon: bool = False,
) -> None:
    ApplyPotionEffectExpression(
        potion=potion,
        duration=duration,
        level=level,
        override_existing_effects=override_existing_effects,
        show_potion_icon=show_potion_icon,
    ).write()
