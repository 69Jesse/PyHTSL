from .writer import WRITER

from .public.function import Function

from typing import Sequence, Any


type Exportable = Function | Sequence[Function] | dict[str, Function | Any]


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
        raise TypeError(f'Expected a Function, Sequence of Functions, or a dict with Function values, got {exportable.__class__.__name__}.')

    if not functions:
        raise ValueError('No functions to export.')

    with WRITER.temporary_container_context(name=name) as container:
        container.registered_functions.extend(functions)
        WRITER.run_export(container)


def disable_global_export() -> None:
    WRITER.export_globally = False
