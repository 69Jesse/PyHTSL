from ..writer import WRITER, LineType


__all__ = (
    'pause_execution',
)


def pause_execution(
    ticks: int = 20,
) -> None:
    WRITER.write(
        f'pause {ticks}',
        LineType.miscellaneous,
    )
