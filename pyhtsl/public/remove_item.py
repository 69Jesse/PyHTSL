from ..writer import WRITER


__all__ = (
    'remove_item',
)


def remove_item(
    item: str,
) -> None:
    WRITER.write(f'removeItem "{item}"')
