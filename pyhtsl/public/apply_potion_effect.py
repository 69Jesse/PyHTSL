from ..writer import WRITER, LineType
from ..types import ALL_POTION_EFFECTS


__all__ = (
    'apply_potion_effect',
)


def apply_potion_effect(
    potion: ALL_POTION_EFFECTS,
    duration: int = 60,
    level: int = 1,
    override_existing_effects: bool = False,
    show_potion_icon: bool = False,
) -> None:
    WRITER.write(
        f'applyPotion "{potion}" {duration} {level} {str(override_existing_effects).lower()} {str(show_potion_icon).lower()}',
        LineType.miscellaneous,
    )
