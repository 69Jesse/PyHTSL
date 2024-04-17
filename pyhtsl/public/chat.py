from ..writer import WRITER, LineType


__all__ = (
    'chat',
)


def chat(
    line: str,
) -> None:
    WRITER.write(
        f'chat "{line}"',
        LineType.miscellaneous,
    )
