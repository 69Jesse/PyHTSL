from ..writer import WRITER


__all__ = (
    'kill_player',
)


def kill_player() -> None:
    WRITER.write('kill')
