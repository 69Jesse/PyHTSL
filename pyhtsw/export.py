from collections.abc import Callable, Sequence
from types import ModuleType
from typing import Any

from .actions.function import Function
from .container import Container
from .importable import Importable

type CallableNoArgs = Callable[[], Any]
type Exportable = Function | CallableNoArgs | Sequence[Exportable] | ModuleType | object


def export(
    exportable: Exportable,
    name: str,
) -> None:
    """Gather every importable reachable from `exportable` — a module, a single
    importable handle (a `@create_function`/`@create_event` result or an
    Item/Menu/Region/NPC subclass), a bare build callback, or any (nested)
    sequence of those — and write them out as a fresh project named `name`.

    A module (or any object) is scanned for attributes carrying a registered
    importable, so handing it a whole module exports exactly the things defined
    in it. Bare callables passed directly are run inside the export container."""
    applies: list[CallableNoArgs] = []
    seen_importables: set[int] = set()
    seen_callables: set[int] = set()

    def add_importable(importable: Importable) -> None:
        if id(importable) in seen_importables:
            return
        seen_importables.add(id(importable))
        applies.append(importable.reexport)

    def add_callable(func: CallableNoArgs) -> None:
        if id(func) in seen_callables:
            return
        seen_callables.add(id(func))
        applies.append(func)

    def extract(exp: Any) -> None:
        importable = getattr(exp, '__htsw_importable__', None)
        if isinstance(importable, Importable):
            add_importable(importable)
            return
        if isinstance(exp, str | bytes):
            return
        if isinstance(exp, Sequence):
            for item in exp:
                extract(item)
            return
        if callable(exp):
            add_callable(exp)
            return
        for attr in dir(exp):
            try:
                value = getattr(exp, attr)
            except Exception:
                continue
            handle = getattr(value, '__htsw_importable__', None)
            if isinstance(handle, Importable):
                add_importable(handle)

    extract(exportable)

    if not applies:
        raise ValueError(
            f'Nothing to export. Double check {exportable!r} of type '
            f'{exportable.__class__.__name__} holds functions, events, items, '
            f'menus, regions or npcs.',
        )

    module_prefix = (
        tuple(exportable.__name__.split('.'))
        if isinstance(exportable, ModuleType)
        else None
    )

    with Container() as container:
        for apply in applies:
            apply()
    container.export(name, module_prefix=module_prefix)
