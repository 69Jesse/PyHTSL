from ..line_type import LineType

from abc import ABC, abstractmethod


__all__ = (
    'Expression',
)


class Expression(ABC):
    def _before_write_line(self) -> None:
        pass

    @abstractmethod
    def _write_line(self) -> tuple[str, LineType]:
        raise NotImplementedError()

    def _after_write_line(self) -> None:
        pass
