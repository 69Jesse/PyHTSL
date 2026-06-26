from collections.abc import Callable

from ..block import NamedBlock
from ..container import get_current_container
from ..importable import EventImportable, EventName
from ..utils.caller import caller_module

__all__ = ('create_event',)


def create_event(
    event: EventName,
) -> Callable[[Callable[[], None]], Callable[[], None]]:
    def decorator(callback: Callable[[], None]) -> Callable[[], None]:
        block = NamedBlock(f'event {event}', callback=callback)
        container = get_current_container()
        container.add_block(block)
        importable = EventImportable(block, event=event)
        importable.module = caller_module()
        container.register_importable(importable)
        callback.__htsw_importable__ = importable  # type: ignore[attr-defined]
        return callback

    return decorator
