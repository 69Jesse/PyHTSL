from ..write import write


__all__ = (
    'reset_inventory',
)


def reset_inventory() -> None:
    write('resetInventory')
