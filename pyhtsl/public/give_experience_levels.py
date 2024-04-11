from ..writer import WRITER


__all__ = (
    'give_experience_levels',
)


def give_experience_levels(
    levels: int,
) -> None:
    WRITER.write(f'xpLevel {levels}')
