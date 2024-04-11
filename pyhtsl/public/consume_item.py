from ..writer import WRITER


__all__ = (
    'consume_item',
)


def consume_item() -> None:
    WRITER.write('consumeItem')
