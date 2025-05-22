
__all__ = (
    'should_display_htsl',
    'display_htsl',
)


DISPLAY_HTSL: bool = False


def should_display_htsl() -> bool:
    return DISPLAY_HTSL


def display_htsl() -> None:
    global DISPLAY_HTSL
    DISPLAY_HTSL = True
