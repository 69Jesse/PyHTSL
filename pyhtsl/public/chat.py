from ..writer import WRITER


__all__ = (
    'chat',
)


def chat(
    line: str,
) -> None:
    WRITER.write(f'chat "{line}"')
