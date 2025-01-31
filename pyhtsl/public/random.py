from ..writer import WRITER, LineType

from typing import Optional
from types import TracebackType


__all__ = (
    'Random',
)


class _Random:
    def __enter__(self) -> None:
        WRITER.write('random {', LineType.random_enter)

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        WRITER.write('}', LineType.random_exit)


Random = _Random()
