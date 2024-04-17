from ..writer import WRITER, LineType


__all__ = (
    'full_heal',
)


def full_heal() -> None:
    WRITER.write(
        'fullHeal',
        LineType.miscellaneous,
    )
