from ..writer import WRITER, LineType


__all__ = (
    'remove_item',
)


def remove_item(
    item: str,
) -> None:
    WRITER.write(
        f'removeItem "{item}"',
        LineType.miscellaneous,
    )
