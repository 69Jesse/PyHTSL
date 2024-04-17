from ..writer import WRITER, LineType


__all__ = (
    'clear_potion_effects',
)


def clear_potion_effects() -> None:
    WRITER.write(
        'clearEffects',
        LineType.miscellaneous,
    )
