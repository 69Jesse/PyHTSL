from ..writer import WRITER


__all__ = (
    'close_menu',
)


def close_menu() -> None:
    WRITER.write('closeMenu')
