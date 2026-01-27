from typing import ClassVar


__all__ = (
    'no_optimization',
    'NoOptimization',
)


def no_optimization() -> bool:
    return NoOptimization.counter > 0


class NoOptimization:
    counter: ClassVar[int] = 0

    def __enter__(self) -> None:
        NoOptimization.counter += 1

    def __exit__(self, *args: object) -> None:
        NoOptimization.counter -= 1
