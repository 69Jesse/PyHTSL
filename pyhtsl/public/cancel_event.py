from ..writer import WRITER


__all__ = (
    'cancel_event',
)


def cancel_event() -> None:
    WRITER.write('cancelEvent')
