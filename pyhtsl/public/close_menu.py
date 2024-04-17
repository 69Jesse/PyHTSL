from ..writer import WRITER, LineType


__all__ = (
    'close_menu',
)


def close_menu() -> None:
    WRITER.write(
        'closeMenu',
        LineType.miscellaneous,
    )
