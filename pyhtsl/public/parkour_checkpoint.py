from ..writer import WRITER, LineType


__all__ = (
    'parkour_checkpoint',
)


def parkour_checkpoint() -> None:
    WRITER.write(
        'parkCheck',
        LineType.miscellaneous,
    )
