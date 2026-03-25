from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..expression.expression import Expression


class ExitSignal(Exception):
    def __init__(self) -> None:
        super().__init__('Exit expression called')


class PauseSignal(Exception):
    ticks: int
    continuation: list['Expression']

    def __init__(self, ticks: int) -> None:
        self.ticks = ticks
        self.continuation = []
        super().__init__(f'Pause for {ticks} ticks')
