import sys
from types import FrameType

__all__ = ('caller_module', 'is_user_frame')

_SKIP_MODULES = frozenset({'types', 'abc'})


def is_user_frame(frame: FrameType) -> bool:
    name = frame.f_globals.get('__name__') or ''
    return (
        name != 'pyhtsw'
        and not name.startswith('pyhtsw.')
        and name not in _SKIP_MODULES
    )


def caller_module() -> str | None:
    """Dotted name of the user module responsible for the current importable.
    Used instead of a callback's or class's own `__module__` so importables
    created by pyhtsw helpers or `types.new_class` are attributed to the user
    code that asked for them, not to pyhtsw/types.

    The first frame outside the pyhtsw package is usually the answer, but a
    *user* factory (`into_special_ability_item(...)`) would claim everything it
    builds for its own module. When that frame is a function, one step further
    out is checked for a module body: at import time that is the module whose
    top level called the factory, which is what owns the importable. A callback
    running at export has no such frame outside it, so it keeps its own module.
    """
    frame: FrameType | None = sys._getframe(1)
    while frame is not None and not is_user_frame(frame):
        frame = frame.f_back
    if frame is None:
        return None
    if frame.f_code.co_name != '<module>':
        outer = frame.f_back
        if (
            outer is not None
            and is_user_frame(outer)
            and outer.f_code.co_name == '<module>'
        ):
            return outer.f_globals.get('__name__') or ''
    return frame.f_globals.get('__name__') or ''
