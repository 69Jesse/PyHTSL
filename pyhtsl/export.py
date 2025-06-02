from .writer import WRITER

from .public.function import Function

from typing import Sequence, Any, Callable
from types import ModuleType


type CallableNoArgs = Callable[[], None | Any]
type Exportable = Function | CallableNoArgs | Sequence[Function | CallableNoArgs] | dict[str, Function | Any] | ModuleType


def export(
    exportable: Exportable,
    name: str,
) -> None:
    callables: list[CallableNoArgs] = []
    if isinstance(exportable, Function):
        if exportable.callback is None:
            raise ValueError(f'Function {exportable} has no callback to export.')
        callables.append(exportable.callback)
    elif callable(exportable):
        callables.append(exportable)
    elif isinstance(exportable, Sequence):
        for item in exportable:
            if isinstance(item, Function):
                if item.callback is None:
                    raise ValueError(f'Function {item} has no callback to export.')
                callables.append(item.callback)
            elif callable(item):
                callables.append(item)
            else:
                raise TypeError(f'Item {item} in sequence is not a Function or callable.')
    elif isinstance(exportable, dict):
        for key, value in exportable.items():
            if isinstance(value, Function):
                if value.callback is None:
                    raise ValueError(f'Function {value} has no callback to export.')
                callables.append(value.callback)
            else:
                raise TypeError(f'Value {value} for key {key} in dict is not a Function or callable.')
    else:
        for attr in dir(exportable):
            value = getattr(exportable, attr)
            if isinstance(value, Function):
                if value.callback is None:
                    raise ValueError(f'Function {value} has no callback to export.')
                callables.append(value.callback)

    if not callables:
        raise ValueError(f'No functions to export. Double check {repr(exportable)} of type {exportable.__class__.__name__} is correct.')

    with WRITER.temporary_container_context(name=name) as container:
        for call in callables:
            call()
        WRITER.run_export(container)


def disable_global_export() -> None:
    WRITER.export_globally = False
