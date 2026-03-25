from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..expression.expression import Expression


__all__ = (
    'ActionScheduler',
    'DelayedActionScheduler',
    'RepeatingActionScheduler',
)


class ActionScheduler:
    def tick(self) -> list['Expression'] | None:
        raise NotImplementedError

    def has_next(self) -> bool:
        raise NotImplementedError


class DelayedActionScheduler(ActionScheduler):
    expressions: list['Expression']
    delay: int

    def __init__(self, expressions: list['Expression'], delay: int) -> None:
        self.expressions = expressions
        self.delay = delay

    def tick(self) -> list['Expression'] | None:
        self.delay -= 1
        if self.delay <= 0:
            return self.expressions
        return None

    def has_next(self) -> bool:
        return self.delay > 0


class RepeatingActionScheduler(ActionScheduler):
    expressions: list['Expression']
    interval: int
    delay: int

    def __init__(self, expressions: list['Expression'], interval: int) -> None:
        self.expressions = expressions
        self.interval = interval
        self.delay = interval

    def tick(self) -> list['Expression'] | None:
        self.delay -= 1
        if self.delay <= 0:
            self.delay = self.interval
            return self.expressions
        return None

    def has_next(self) -> bool:
        return True
