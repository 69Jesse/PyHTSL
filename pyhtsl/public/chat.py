from ..write import write


__all__ = (
    'chat',
)


def chat(
    line: str,
) -> None:
    write(f'chat "{line}"')
