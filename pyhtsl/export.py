from .public.function import Function
from .container import Container

from typing import Sequence, Any, Callable
from types import ModuleType


type CallableNoArgs = Callable[[], Any]
type Exportable = (
    Function[Callable[[], None]]
    | CallableNoArgs
    | Sequence[Exportable]
    | dict[str, Exportable]
    | ModuleType
)


def export(
    exportable: Exportable,
    name: str,
) -> None:
    callables: list[CallableNoArgs] = []

    def extract_function(exp: Any) -> None:
        if not isinstance(exp, Function):
            return
        if exp.callback is None:
            return
        callables.append(exp.callback)

    def extract_recursive(exp: Exportable) -> None:
        if isinstance(exp, Function):
            if exp.callback is None:
                return
            callables.append(exp.callback)
        elif callable(exp):
            callables.append(exp)
        elif isinstance(exp, Sequence):
            for item in exp:
                extract_recursive(item)
        elif isinstance(exp, dict):
            for value in exp.values():
                extract_function(value)
        else:
            for attr in dir(exp):
                value = getattr(exp, attr)
                extract_function(value)

    extract_recursive(exportable)

    if not callables:
        raise ValueError(
            f'No functions to export. Double check {repr(exportable)} of type {exportable.__class__.__name__} is correct.'
        )

    with Container(name=name) as container:
        for call in callables:
            call()
        container.export()
