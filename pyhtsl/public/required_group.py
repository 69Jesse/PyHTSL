from ..condition import TinyCondition
from .group import Group

from typing import final


__all__ = (
    'RequiredGroup',
)


@final
class RequiredGroup(TinyCondition):
    group: Group
    include_higher_groups: bool
    def __init__(
        self,
        group: Group | str,
        include_higher_groups: bool = False,
    ) -> None:
        self.group = group if isinstance(group, Group) else Group(group)
        self.include_higher_groups = include_higher_groups

    def create_line(self) -> str:
        return f'hasGroup "{self.group.name}" {str(self.include_higher_groups).lower()}'
