from ..writer import WRITER


__all__ = (
    'exit_function',
)


def exit_function() -> None:
    WRITER.write('exit')
