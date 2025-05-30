from ..writer import WRITER, LineType

from types import TracebackType


__all__ = (
    'Random',
)


class _Random:
    def __enter__(self) -> None:
        WRITER.write('random {', LineType.random_enter)
        WRITER.begin_indent()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        WRITER.end_indent()
        WRITER.write('}', LineType.random_exit)


Random = _Random()
