from ..writer import WRITER, LineType


__all__ = ('cancel_event',)


def cancel_event() -> None:
    WRITER.write(
        'cancelEvent',
        LineType.cancel_event,
    )
