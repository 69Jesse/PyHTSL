from ..writer import WRITER, LineType
from .group import Group

__all__ = ('change_player_group',)


def change_player_group(
    group: Group | str,
    demotion_protection: bool = True,
) -> None:
    group = group if isinstance(group, Group) else Group(group)
    WRITER.write(
        f'changePlayerGroup "{group.name}" {str(demotion_protection).lower()}',
        LineType.miscellaneous,
    )
