"""Shared helpers for the test suite."""

from collections.abc import Iterator
from contextlib import contextmanager

__all__ = ('expect_exception',)


@contextmanager
def expect_exception(*exception_classes: type[BaseException]) -> Iterator[None]:
    """Assert that the wrapped block raises one of ``exception_classes``.

    Raises ``AssertionError`` on ``__exit__`` if nothing was raised. Any
    exception not matching ``exception_classes`` propagates unchanged.
    """
    if not exception_classes:
        raise ValueError('expect_exception requires at least one exception class')
    try:
        yield
    except exception_classes:
        return
    names = ', '.join(c.__name__ for c in exception_classes)
    raise AssertionError(f'expected {names} to be raised, but no exception was raised')
