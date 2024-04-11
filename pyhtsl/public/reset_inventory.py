from ..writer import WRITER


__all__ = (
    'reset_inventory',
)


def reset_inventory() -> None:
    WRITER.write('resetInventory')
