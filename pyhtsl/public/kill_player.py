from ..writer import WRITER, LineType


__all__ = ('kill_player',)


def kill_player() -> None:
    WRITER.write(
        'kill',
        LineType.miscellaneous,
    )
