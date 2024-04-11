from ..writer import WRITER


__all__ = (
    'fail_parkour',
)


def fail_parkour(
    reason: str = 'Failed!',
) -> None:
    WRITER.write(f'failParkour "{reason}"')
