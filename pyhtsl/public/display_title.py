from ..writer import WRITER, LineType


__all__ = (
    'display_title',
)


def display_title(
    title: str,
    subtitle: str = '',
    fadein: int = 1,
    stay: int = 5,
    fadeout: int = 1,
) -> None:
    WRITER.write(
        f'title "{title or '&r'}" "{subtitle or '&r'}" {fadein} {stay} {fadeout}',
        LineType.miscellaneous,
    )
