import sys

__all__ = ('caller_module',)

_SKIP_MODULES = frozenset({'types', 'abc'})


def caller_module() -> str | None:
    """Dotted name of the first frame outside the pyhtsw package (and the class
    machinery) — the user module responsible for the current importable. Used
    instead of a callback's or class's own `__module__` so importables created
    by pyhtsw helpers or `types.new_class` are attributed to the user code that
    asked for them, not to pyhtsw/types."""
    frame = sys._getframe(1)
    while frame is not None:
        name = frame.f_globals.get('__name__') or ''
        if (
            name != 'pyhtsw'
            and not name.startswith('pyhtsw.')
            and name not in _SKIP_MODULES
        ):
            return name
        frame = frame.f_back
    return None
