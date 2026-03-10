from abc import abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, final

from ..base_object import BaseObject
from ..container import get_current_container

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext
    from ..stats.stat import Stat


__all__ = ('Expression',)


class Expression(BaseObject):
    def into_executable_expressions(self) -> Generator['Expression', None, None]:
        yield self

    @abstractmethod
    def into_htsl(self) -> str:
        raise NotImplementedError()

    def write(self) -> None:
        get_current_container().write_expression(self.cloned())

    def raw_execute(self, context: 'ExecutionContext') -> None:
        print(f'No execution defined for expression "{self!r}"')

    @final
    def execute(self, context: 'ExecutionContext') -> None:
        if context.expression_callback is not None:
            context.expression_callback(self)
        if context.verbose:
            print(f'Executing expression "{self!r}"')
        self.raw_execute(context)

    def _get_all_values(self) -> dict[str, Any]:
        return vars(self)

    def get_all_stats_used(self) -> dict[str, 'Stat']:
        from ..stats.stat import Stat

        stats: dict[str, Stat] = {}
        for key, value in self._get_all_values().items():
            if isinstance(value, Stat):
                stats[key] = value
        return stats

    def is_using_stat(self, stat: 'Stat') -> bool:
        return any(s.is_same_stat(stat) for s in self.get_all_stats_used().values())

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
        for key, value in self.get_all_stats_used().items():
            if not value.is_same_stat(old_stat):
                continue
            setattr(self, key, new_stat)
            has_changed = True
        return has_changed

    def walk_expressions(self) -> Generator['Expression', None, None]:
        yield self
