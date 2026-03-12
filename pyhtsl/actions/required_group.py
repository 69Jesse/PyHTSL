from typing import Self, final

from ..expression.condition.condition import Condition
from .group import Group

__all__ = ('RequiredGroup',)


@final
class RequiredGroup(Condition):
    group: Group
    include_higher_groups: bool

    def __init__(
        self,
        group: Group | str,
        include_higher_groups: bool = False,
    ) -> None:
        self.group = group if isinstance(group, Group) else Group(group)
        self.include_higher_groups = include_higher_groups

    def into_htsl_raw(self) -> str:
        return f'hasGroup {self.inline_quoted(self.group.name)} {self.inline(self.include_higher_groups)}'

    def cloned_raw(self) -> Self:
        return self.__class__(
            group=self.group.cloned(),
            include_higher_groups=self.include_higher_groups,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, RequiredGroup):
            return False
        return (
            self.group.equals(other.group)
            and self.include_higher_groups == other.include_higher_groups
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<group={self.group!r} include_higher_groups={self.include_higher_groups} inverted={self.inverted}>'
