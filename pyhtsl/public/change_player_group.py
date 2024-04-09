from .group import Group
from ..write import write


__all__ = (
    'change_player_group',
)


def change_player_group(
    group: Group | str,
    demotion_protection: bool = True,
) -> None:
    group = group if isinstance(group, Group) else Group(group)
    write(f'changePlayerGroup "{group.name}" {str(demotion_protection).lower()}')
