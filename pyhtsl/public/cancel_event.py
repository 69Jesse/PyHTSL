from ..write import write


__all__ = (
    'cancel_event',
)


def cancel_event() -> None:
    write('cancelEvent')
