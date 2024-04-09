from ..write import write


__all__ = (
    'pause_execution',
)


def pause_execution(
    ticks: int = 20,
) -> None:
    write(f'pause {ticks}')
