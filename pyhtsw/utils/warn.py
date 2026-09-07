import sys
import warnings
from types import FrameType
from typing import NamedTuple

from pyhtsw.utils.caller import is_user_frame

__all__ = ('PyHTSWWarning', 'SourceSite', 'consumer_site', 'warn', 'warn_at')


class PyHTSWWarning(UserWarning):
    """Every warning pyhtsw raises about the consumer's own source."""


class SourceSite(NamedTuple):
    filename: str
    lineno: int


def _consumer_frame() -> tuple[FrameType | None, int]:
    frame: FrameType | None = sys._getframe(1)
    depth = 1
    while frame is not None and not is_user_frame(frame):
        frame = frame.f_back
        depth += 1
    return frame, depth


def consumer_site() -> SourceSite | None:
    frame, _ = _consumer_frame()
    if frame is None:
        return None
    return SourceSite(frame.f_code.co_filename, frame.f_lineno)


def warn(message: str) -> None:
    _, depth = _consumer_frame()
    warnings.warn(message, PyHTSWWarning, stacklevel=depth)


def warn_at(message: str, site: SourceSite | None) -> None:
    if site is None:
        warn(message)
        return
    warnings.warn_explicit(message, PyHTSWWarning, site.filename, site.lineno)
