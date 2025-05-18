from ..expression.handler import AUTOMATIC_UNSET

from typing import Optional
from types import TracebackType


__all__ = (
    'disable_automatic_unset',
)


class disable_automatic_unset:
    def __init__(self) -> None:
        AUTOMATIC_UNSET.increment()

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        AUTOMATIC_UNSET.decrement()
