from abc import abstractmethod
from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Any, final

from ..base_object import BaseObject
from ..container import Container, get_current_container
from ..utils.log import log

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext
    from ..stats.stat import Stat


__all__ = ('Expression',)


# Lazily cached to dodge import cycles; these are only touched well after every
# module is loaded, and resolving them once avoids re-running `from` import
# machinery on the millions of calls the optimizer makes.
_Stat: type | None = None
_Checkable: type | None = None
_TemporaryStat: type | None = None


def _stat_refs() -> tuple[type, type, type]:
    global _Stat, _Checkable, _TemporaryStat
    if _Stat is None:
        from ..checkable import Checkable
        from ..stats.stat import Stat
        from ..stats.temporary_stat import TemporaryStat

        _Stat, _Checkable, _TemporaryStat = Stat, Checkable, TemporaryStat
    return _Stat, _Checkable, _TemporaryStat  # type: ignore[return-value]


class Expression(BaseObject):
    def into_executable_expressions(self) -> Generator['Expression']:
        yield self

    @abstractmethod
    def into_htsl(self) -> str:
        raise NotImplementedError()

    def write(self) -> None:
        get_current_container().write_expression(self.cloned())

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(
            f'No execution implemented for expression \x1b[38;2;255;0;0m"{self!r}"\x1b[0m',
        )

    @final
    def execute(self, context: 'ExecutionContext') -> None:
        if context.expression_callback is not None:
            context.expression_callback(self)
        if context.verbose:
            log(f'Executing expression \x1b[38;2;255;0;0m"{self!r}"\x1b[0m')
        self.raw_execute(context)

    def _get_all_values(self) -> dict[str, Any]:
        return vars(self)

    def get_all_stats_used(
        self,
    ) -> Generator[tuple['Stat', Callable[['Stat'], None]]]:
        Stat, _, _ = _stat_refs()

        for key, value in self._get_all_values().items():
            if isinstance(value, Stat):
                yield (value, lambda new, _key=key: setattr(self, _key, new))

    def is_using_stat(self, stat: 'Stat') -> bool:
        Stat, Checkable, TemporaryStat = _stat_refs()

        string_stat = (
            stat.into_player_stat() if isinstance(stat, TemporaryStat) else stat
        )

        for expr in self.walk_expressions():
            for s, _ in expr.get_all_stats_used():
                if s.is_same_stat(stat):
                    return True
            # Stats can also be referenced by their placeholders inside string fields, kind of hacky but whatever
            for value in expr._get_all_values().values():
                if not isinstance(value, str):
                    continue
                for ref in Checkable.iter_in_string(value):
                    if isinstance(ref, Stat) and ref.is_same_stat(string_stat):
                        return True
        return False

    def is_using_stats_together(
        self,
        stat1: 'Stat',
        stat2: 'Stat',
    ) -> bool:
        return self.is_using_stat(stat1) and self.is_using_stat(stat2)

    def change_all_occurrences_of_stat(
        self,
        old_stat: 'Stat',
        new_stat: 'Stat',
    ) -> bool:
        has_changed: bool = False
        for expr in self.walk_expressions():
            for value, setter in expr.get_all_stats_used():
                if not value.is_same_stat(old_stat):
                    continue
                setter(new_stat)
                has_changed = True
        return has_changed

    def walk_expressions(self) -> Generator['Expression']:
        yield self

    def finalize(self, container: Container) -> None:
        self.into_htsl()

    def nested_expressions_refs(self) -> list[list['Expression']]:
        return []

    def can_be_nested(self) -> bool:
        return len(self.nested_expressions_refs()) == 0

    def describe_nestable_block(self) -> str:
        return repr(self)

    def nestable_block_detail_lines(self) -> list[str]:
        return []
