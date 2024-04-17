from ..writer import WRITER, LineType


__all__ = (
    'reset_inventory',
)


def reset_inventory() -> None:
    WRITER.write(
        'resetInventory',
        LineType.miscellaneous,
    )
