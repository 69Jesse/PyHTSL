from ..writer import WRITER, LineType


__all__ = ('give_experience_levels',)


def give_experience_levels(
    levels: int,
) -> None:
    WRITER.write(
        f'xpLevel {levels}',
        LineType.miscellaneous,
    )
