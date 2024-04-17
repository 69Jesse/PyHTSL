from ..writer import WRITER, LineType


__all__ = (
    'consume_item',
)


def consume_item() -> None:
    WRITER.write(
        'consumeItem',
        LineType.miscellaneous,
    )
