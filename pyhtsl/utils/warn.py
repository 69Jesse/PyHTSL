import inspect
import os
import warnings

PACKAGE_DIR: str = os.path.dirname(os.path.abspath(__file__))


def warn(message: str) -> None:
    frame = inspect.currentframe()
    assert frame is not None
    stacklevel = 1
    while frame is not None:
        filename = os.path.abspath(frame.f_code.co_filename)
        if not filename.startswith(PACKAGE_DIR):
            break
        stacklevel += 1
        frame = frame.f_back
    warnings.warn(message, stacklevel=stacklevel)
