from ..writer import WRITER


__all__ = (
    'parkour_checkpoint',
)


def parkour_checkpoint() -> None:
    WRITER.write('parkCheck')
