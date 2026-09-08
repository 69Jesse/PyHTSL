from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, overload

from pyhtsw.actions.flow import IfAll, exit_function, trigger_function
from pyhtsw.declarations.function import Function, function
from pyhtsw.editable import Editable, HousingType
from pyhtsw.ext.array_read_write import MaybeSequence, into_sequence
from pyhtsw.placeholders.house import HousePlayers
from pyhtsw.stats.global_stat import GlobalStat

if TYPE_CHECKING:
    from pyhtsw.declarations.item import Item

__all__ = ('Gatherer', 'gather_from_all_players')

_DEFAULT_COUNTER = GlobalStat('gathered').as_long()


class Gatherer:
    """A function that runs for every player so the caller can read what they
    collectively wrote."""

    def __init__(
        self,
        target: Function,
        *,
        counter: Editable | None,
    ) -> None:
        self.target = target
        self.counter = counter

    @contextmanager
    def gather(
        self,
        *,
        reset: MaybeSequence[Editable] = (),
        to: MaybeSequence[HousingType] = 0,
    ) -> Generator[None]:
        """Clear the accumulators, run the body for everyone, and hand control
        back with the result available.

        Everything is emitted on entry; the ``with`` marks the region where the
        gathered value means something.
        """
        targets = list(into_sequence(reset))
        seeds = list(into_sequence(to))
        if len(seeds) == 1:
            seeds *= len(targets)
        for target, seed in zip(targets, seeds, strict=True):
            target.value = seed
        if self.counter is not None:
            self.counter.value = 0
        trigger_function(self.target, trigger_for_all_players=True)
        if self.counter is not None:
            # A player who did not report yet leaves the total wrong, so the
            # caller waits for the next tick rather than acting on it.
            with IfAll(self.counter != HousePlayers):
                exit_function()
        yield


@overload
def gather_from_all_players(name: Callable[[], None], /) -> Gatherer: ...


@overload
def gather_from_all_players(
    name: str,
    /,
    *,
    require_all: bool = ...,
    counter: Editable | None = ...,
    icon: 'Item | None' = ...,
) -> Callable[[Callable[[], None]], Gatherer]: ...


def gather_from_all_players(
    name: str | Callable[[], None],
    /,
    *,
    require_all: bool = False,
    counter: Editable | None = None,
    icon: 'Item | None' = None,
) -> Gatherer | Callable[[Callable[[], None]], Gatherer]:
    """Declare the per-player half of a gather.

    With ``require_all`` the function also counts itself, so the caller can
    refuse to read a partial result.
    """
    if callable(name):
        raise TypeError('gather_from_all_players needs the function name')

    tally = (counter or _DEFAULT_COUNTER) if require_all else None

    def decorator(callback: Callable[[], None]) -> Gatherer:
        @function(name, icon=icon)
        def target() -> None:
            if tally is not None:
                tally.value += 1
            callback()

        return Gatherer(target, counter=tally)

    return decorator
