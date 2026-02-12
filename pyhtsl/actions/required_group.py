from typing import final

from ..condition.base_condition import BaseCondition
from .group import Group

__all__ = ('RequiredGroup',)


@final
class RequiredGroup(BaseCondition):
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
        return f'hasGroup "{self.group.name}" {str(self.include_higher_groups).lower()}'
