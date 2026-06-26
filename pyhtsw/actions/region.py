from collections.abc import Callable
from typing import Any, ClassVar

from ..block import NamedBlock
from ..container import get_current_container
from ..importable import Bounds, Handler, RegionImportable, call_with_args
from ..utils.caller import caller_module

__all__ = ('Region',)


def _on_enter(func: Callable[..., Any]) -> Callable[..., Any]:
    func.__htsw_region__ = 'enter'  # type: ignore[attr-defined]
    return func


def _on_exit(func: Callable[..., Any]) -> Callable[..., Any]:
    func.__htsw_region__ = 'exit'  # type: ignore[attr-defined]
    return func


class Region:
    __htsw_name__: ClassVar[str | None] = None
    __htsw_importable__: ClassVar[RegionImportable]

    on_enter = staticmethod(_on_enter)
    on_exit = staticmethod(_on_exit)

    def __init_subclass__(
        cls,
        bounds: Bounds | None = None,
        on_enter: Handler | None = None,
        on_exit: Handler | None = None,
    ) -> None:
        super().__init_subclass__()
        cls.__htsw_name__ = cls.__name__

        enter_fn = on_enter
        exit_fn = on_exit
        for value in vars(cls).values():
            tag = getattr(value, '__htsw_region__', None)
            if tag == 'enter':
                enter_fn = value
            elif tag == 'exit':
                exit_fn = value

        container = get_current_container()
        enter_block = exit_block = None
        if enter_fn is not None:
            handler = enter_fn
            enter_block = NamedBlock(
                f'{cls.__name__} enter',
                callback=lambda: call_with_args(handler, None),
            )
            container.add_block(enter_block)
        if exit_fn is not None:
            handler = exit_fn
            exit_block = NamedBlock(
                f'{cls.__name__} exit',
                callback=lambda: call_with_args(handler, None),
            )
            container.add_block(exit_block)

        importable = RegionImportable(
            name=cls.__name__,
            bounds=bounds,
            on_enter=enter_block,
            on_exit=exit_block,
        )
        importable.module = caller_module()
        container.register_importable(importable)
        cls.__htsw_importable__ = importable
