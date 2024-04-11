from ..writer import WRITER


__all__ = (
    'pause_execution',
)


def pause_execution(
    ticks: int = 20,
) -> None:
    WRITER.write(f'pause {ticks}')
