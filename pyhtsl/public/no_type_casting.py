from typing import ClassVar


__all__ = (
    'no_type_casting',
    'NoTypeCasting',
)


def no_type_casting() -> bool:
    return NoTypeCasting.counter > 0


class NoTypeCasting:
    counter: ClassVar[int] = 0
    def __enter__(self) -> None:
        NoTypeCasting.counter += 1

    def __exit__(self, *args: object) -> None:
        NoTypeCasting.counter -= 1
