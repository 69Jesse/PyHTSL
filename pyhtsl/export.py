from .writer import WRITER

from .public.function import Function

from typing import Sequence, Any
from types import ModuleType


type Exportable = Function | Sequence[Function] | dict[str, Function | Any] | ModuleType


def export(
    exportable: Exportable,
    name: str,
) -> None:
    if isinstance(exportable, Function):
        functions = [exportable]
    elif isinstance(exportable, Sequence):
        functions = list(exportable)
        for func in functions:
            if not isinstance(func, Function):
                raise TypeError(f'Expected a Function, got {func.__class__.__name__}.')
    elif isinstance(exportable, dict):
        functions = [v for v in exportable.values() if isinstance(v, Function)]
    else:
        functions = []
        for attr in dir(exportable):
            value = getattr(exportable, attr)
            if isinstance(value, Function):
                functions.append(value)

    if not functions:
        raise ValueError(f'No functions to export. Double check {repr(exportable)} of type {exportable.__class__.__name__} is correct.')

    with WRITER.temporary_container_context(name=name) as container:
        container.registered_functions.extend(functions)
        WRITER.run_export(container)


def disable_global_export() -> None:
    WRITER.export_globally = False
