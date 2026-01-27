from ..writer import WRITER, LineType


__all__ = ('fail_parkour',)


def fail_parkour(
    reason: str = 'Failed!',
) -> None:
    WRITER.write(
        f'failParkour "{reason}"',
        LineType.miscellaneous,
    )
