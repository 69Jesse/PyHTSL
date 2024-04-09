from ..write import write


__all__ = (
    'send_to_lobby',
)


def send_to_lobby(
    lobby: str,
) -> None:
    write(f'lobby "{lobby}"')
