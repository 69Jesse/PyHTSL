from ..write import write


__all__ = (
    'remove_item',
)


def remove_item(
    item: str,
) -> None:
    write(f'removeItem "{item}"')
