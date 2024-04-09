from ..write import write


__all__ = (
    'fail_parkour',
)


def fail_parkour(
    reason: str = 'Failed!',
) -> None:
    write(f'failParkour "{reason}"')
