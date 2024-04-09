from ..write import write


__all__ = (
    'give_experience_levels',
)


def give_experience_levels(
    levels: int,
) -> None:
    write(f'xpLevel {levels}')
