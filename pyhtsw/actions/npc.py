from typing import ClassVar

from ..block import NamedBlock
from ..container import get_current_container
from ..importable import (
    Coord,
    Handler,
    NpcEquipment,
    NpcImportable,
    NpcSkin,
    call_with_args,
)
from .item import left_click, right_click

__all__ = ('NPC',)


class NPC:
    Equipment = NpcEquipment

    __htsw_name__: ClassVar[str | None] = None
    __htsw_importable__: ClassVar[NpcImportable]

    left_click = staticmethod(left_click)
    right_click = staticmethod(right_click)

    def __init_subclass__(
        cls,
        pos: Coord,
        on_left_click: Handler | None = None,
        on_right_click: Handler | None = None,
        look_at_players: bool | None = None,
        hide_name_tag: bool | None = None,
        skin: NpcSkin | None = None,
        equipment: NpcEquipment | None = None,
    ) -> None:
        super().__init_subclass__()
        cls.__htsw_name__ = cls.__name__

        left_fn = on_left_click
        right_fn = on_right_click
        for value in vars(cls).values():
            tag = getattr(value, '__htsw_click__', None)
            if tag == 'left':
                left_fn = value
            elif tag == 'right':
                right_fn = value

        container = get_current_container()
        left_block = right_block = None
        if left_fn is not None:
            handler = left_fn
            left_block = NamedBlock(
                f'{cls.__name__} left',
                callback=lambda: call_with_args(handler, None),
            )
            container.add_block(left_block)
        if right_fn is not None:
            handler = right_fn
            right_block = NamedBlock(
                f'{cls.__name__} right',
                callback=lambda: call_with_args(handler, None),
            )
            container.add_block(right_block)

        importable = NpcImportable(
            name=cls.__name__,
            pos=pos,
            left=left_block,
            right=right_block,
            look_at_players=look_at_players,
            hide_name_tag=hide_name_tag,
            skin=skin,
            equipment=equipment,
        )
        importable.module = cls.__module__
        container.register_importable(importable)
        cls.__htsw_importable__ = importable
