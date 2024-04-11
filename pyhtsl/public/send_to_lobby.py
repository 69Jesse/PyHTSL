from ..writer import WRITER


__all__ = (
    'send_to_lobby',
)


def send_to_lobby(
    lobby: str,
) -> None:
    WRITER.write(f'lobby "{lobby}"')
