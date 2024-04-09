from ..write import write


__all__ = (
    'kill_player',
)


def kill_player() -> None:
    write('kill')
