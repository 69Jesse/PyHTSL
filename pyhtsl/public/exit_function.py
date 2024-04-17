from ..writer import WRITER, LineType


__all__ = (
    'exit_function',
)


def exit_function() -> None:
    WRITER.write(
        'exit',
        LineType.exit_function,
    )
