from collections.abc import Callable

__all__ = ('call_with_optional_arg',)


def call_with_optional_arg[A, T](
    callback: Callable[[], T] | Callable[[A], T],
    arg: A,
    *,
    noun: str = 'callable',
) -> T:
    code = callback.__code__
    defaults = callback.__defaults__ or ()
    required = code.co_argcount - len(defaults)
    if required == 0:
        return callback()  # pyright: ignore[reportCallIssue]
    if required == 1:
        return callback(arg)  # pyright: ignore[reportCallIssue]
    raise ValueError(
        f'Callable {noun} must take 0 or 1 required arguments, got {required}'
    )
