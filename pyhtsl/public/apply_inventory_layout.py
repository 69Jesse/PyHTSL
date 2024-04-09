from ..write import write
from .layout import Layout


__all__ = (
    'apply_inventory_layout',
)


def apply_inventory_layout(
    layout: Layout | str,
) -> None:
    layout = layout if isinstance(layout, Layout) else Layout(layout)
    write(f'applyLayout "{layout.name}"')
