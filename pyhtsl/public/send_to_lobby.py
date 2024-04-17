from ..writer import WRITER, LineType


__all__ = (
    'send_to_lobby',
)


def send_to_lobby(
    lobby: str,
) -> None:
    WRITER.write(
        f'lobby "{lobby}"',
        LineType.miscellaneous,
    )
