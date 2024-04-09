from ..write import write

from typing import Literal


__all__ = (
    'give_item',
)


def give_item(
    item: str,
    allow_multiple: bool = False,
    inventory_slot: Literal[
        'first_slot',
        'hand_slot',
        'hotbar_slot_1',
        'hotbar_slot_2',
        'hotbar_slot_3',
        'hotbar_slot_4',
        'hotbar_slot_5',
        'hotbar_slot_6',
        'hotbar_slot_7',
        'hotbar_slot_8',
        'hotbar_slot_9',
        'inventory_slot_1',
        'inventory_slot_2',
        'inventory_slot_3',
        'inventory_slot_4',
        'inventory_slot_5',
        'inventory_slot_6',
        'inventory_slot_7',
        'inventory_slot_8',
        'inventory_slot_9',
        'inventory_slot_10',
        'inventory_slot_11',
        'inventory_slot_12',
        'inventory_slot_13',
        'inventory_slot_14',
        'inventory_slot_15',
        'inventory_slot_16',
        'inventory_slot_17',
        'inventory_slot_18',
        'inventory_slot_19',
        'inventory_slot_20',
        'inventory_slot_21',
        'inventory_slot_22',
        'inventory_slot_23',
        'inventory_slot_24',
        'inventory_slot_25',
        'inventory_slot_26',
        'inventory_slot_27',
        'helmet',
        'chestplate',
        'leggings',
        'boots',
    ] = 'first_slot',
    replace_existing_item: bool = False,
) -> None:
    write(f'giveItem "{item}" {str(allow_multiple).lower()} {inventory_slot} {str(replace_existing_item).lower()}')
