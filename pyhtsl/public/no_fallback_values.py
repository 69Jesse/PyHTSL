from typing import ClassVar


__all__ = (
    'no_fallback_values',
    'NoFallbackValues',
)


def no_fallback_values() -> bool:
    return NoFallbackValues.counter > 0


class NoFallbackValues:
    counter: ClassVar[int] = 0
    def __enter__(self) -> None:
        NoFallbackValues.counter += 1

    def __exit__(self, *args: object) -> None:
        NoFallbackValues.counter -= 1
