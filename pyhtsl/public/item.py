from ..writer import HERE, HTSL_IMPORTS_FOLDER
from .enchantment import ALL_POSSIBLE_ENCHANTMENTS, Enchantment, ENCHANTMENT_TO_ID

import json
import re
from enum import Enum
import hashlib
import difflib

from typing import Literal, TypedDict, overload, Iterable, Optional, Any, Callable


__all__ = (
    'Item',
)


class ItemJsonData(TypedDict):
    key: str
    title: str
    name: str
    id: int
    data_value: int
    can_be_damaged: bool


ITEMS_JSON_FILE = HERE / 'misc' / 'items.json'
with ITEMS_JSON_FILE.open('r', encoding='utf-8') as file:
    ITEMS: dict[str, ItemJsonData] = json.load(file)


HIDE_FLAGS: dict[str, int] = {
    'hide_enchantments_flag': 1,
    'hide_modifiers_flag': 2,
    'hide_unbreakable_flag': 4,
    # 'hide_can_destroy_flag': 8,    # Not sure what these do and if theyre actually implemented, if they are let me know..
    # 'hide_can_place_on_flag': 16,  #
    'hide_additional_flag': 32,
    'hide_dye_flag': 64,
}
HIDE_FLAGS['hide_all_flags'] = max(HIDE_FLAGS.values()) * 2 - 1


class DataTypeCallback:
    callback: Callable[[Any], str]
    def __init__(self, callback: Callable[[Any], str]) -> None:
        self.callback = callback

    def __call__(self, value: Any) -> str:
        return self.callback(value)


class DataType(Enum):
    byte = DataTypeCallback(lambda x: f'{x}b')
    short = DataTypeCallback(lambda x: f'{x}s')
    integer = DataTypeCallback(lambda x: f'{x}')
    string = DataTypeCallback(lambda x: '\\"' + x.replace('"', '\\"') + '\\"')


NON_SPECIAL_ITEM_KEYS = Literal[
    'stone', 'granite', 'polished_granite', 'diorite', 'polished_diorite', 'andesite', 'polished_andesite', 'grass_block',
    'dirt', 'coarse_dirt', 'podzol', 'cobblestone', 'oak_planks', 'spruce_planks', 'birch_planks', 'jungle_planks',
    'acacia_planks', 'dark_oak_planks', 'oak_sapling', 'spruce_sapling', 'birch_sapling', 'jungle_sapling', 'acacia_sapling', 'dark_oak_sapling',
    'bedrock', 'sand', 'red_sand', 'gravel', 'gold_ore', 'iron_ore', 'coal_ore', 'oak_log',
    'spruce_log', 'birch_log', 'jungle_log', 'oak_leaves', 'spruce_leaves', 'birch_leaves', 'jungle_leaves', 'sponge',
    'wet_sponge', 'glass', 'lapis_lazuli_ore', 'lapis_lazuli_block', 'dispenser', 'sandstone', 'chiseled_sandstone', 'smooth_sandstone',
    'note_block', 'powered_rails', 'detector_rails', 'sticky_piston', 'cobweb', 'grass', 'fern', 'dead_bush',
    'piston', 'white_wool', 'orange_wool', 'magenta_wool', 'light_blue_wool', 'yellow_wool', 'lime_wool', 'pink_wool',
    'gray_wool', 'light_gray_wool', 'cyan_wool', 'purple_wool', 'blue_wool', 'brown_wool', 'green_wool', 'red_wool',
    'black_wool', 'dandelion', 'poppy', 'blue_orchid', 'allium', 'azure_bluet', 'red_tulip', 'orange_tulip',
    'white_tulip', 'pink_tulip', 'oxeye_daisy', 'brown_mushroom', 'red_mushroom', 'block_of_gold', 'block_of_iron', 'stone_slab',
    'sandstone_slab', 'cobblestone_slab', 'brick_slab', 'stone_brick_slab', 'nether_brick_slab', 'quartz_slab', 'bricks', 'tnt',
    'bookshelf', 'mossy_cobblestone', 'obsidian', 'torch', 'monster_spawner', 'oak_stairs', 'chest', 'diamond_ore',
    'block_of_diamond', 'crafting_table', 'farmland', 'furnace', 'ladder', 'rails', 'cobblestone_stairs', 'lever',
    'stone_pressure_plate', 'oak_pressure_plate', 'redstone_ore', 'redstone_torch', 'stone_button', 'snow', 'ice', 'snow_block',
    'cactus', 'clay_block', 'jukebox', 'oak_fence', 'pumpkin', 'netherrack', 'soul_sand', 'glowstone',
    'jack_o_lantern', 'white_stained_glass', 'orange_stained_glass', 'magenta_stained_glass', 'light_blue_stained_glass', 'yellow_stained_glass', 'lime_stained_glass', 'pink_stained_glass',
    'gray_stained_glass', 'light_gray_stained_glass', 'cyan_stained_glass', 'purple_stained_glass', 'blue_stained_glass', 'brown_stained_glass', 'green_stained_glass', 'red_stained_glass',
    'black_stained_glass', 'oak_trapdoor', 'infested_stone', 'infested_cobblestone', 'infested_stone_bricks', 'infested_mossy_stone_bricks', 'infested_cracked_stone_bricks', 'infested_chiseled_stone_bricks',
    'stone_bricks', 'mossy_stone_bricks', 'cracked_stone_bricks', 'chiseled_stone_bricks', 'brown_mushroom_block', 'red_mushroom_block', 'iron_bars', 'glass_pane',
    'block_of_melon', 'vines', 'oak_fence_gate', 'brick_stairs', 'stone_brick_stairs', 'mycelium', 'lily_pad', 'block_of_nether_bricks',
    'nether_brick_fence', 'nether_brick_stairs', 'enchanting_table', 'end_portal_frame', 'end_stone', 'dragon_egg', 'redstone_lamp', 'oak_slab',
    'spruce_slab', 'birch_slab', 'jungle_slab', 'acacia_slab', 'dark_oak_slab', 'sandstone_stairs', 'emerald_ore', 'ender_chest',
    'tripwire_hook', 'block_of_emerald', 'spruce_stairs', 'birch_stairs', 'jungle_stairs', 'command_block', 'beacon', 'cobblestone_wall',
    'mossy_cobblestone_wall', 'oak_button', 'anvil', 'slightly_damaged_anvil', 'very_damaged_anvil', 'trapped_chest', 'light_weighted_pressure_plate', 'heavy_weighted_pressure_plate',
    'daylight_detector', 'block_of_redstone', 'nether_quartz_ore', 'hopper', 'block_of_quartz', 'chiseled_quartz_block', 'quartz_pillar', 'quartz_stairs',
    'activator_rails', 'dropper', 'white_terracotta', 'orange_terracotta', 'magenta_terracotta', 'light_blue_terracotta', 'yellow_terracotta', 'lime_terracotta',
    'pink_terracotta', 'gray_terracotta', 'light_gray_terracotta', 'cyan_terracotta', 'purple_terracotta', 'blue_terracotta', 'brown_terracotta', 'green_terracotta',
    'red_terracotta', 'black_terracotta', 'white_stained_glass_pane', 'orange_stained_glass_pane', 'magenta_stained_glass_pane', 'light_blue_stained_glass_pane', 'yellow_stained_glass_pane', 'lime_stained_glass_pane',
    'pink_stained_glass_pane', 'gray_stained_glass_pane', 'light_gray_stained_glass_pane', 'cyan_stained_glass_pane', 'purple_stained_glass_pane', 'blue_stained_glass_pane', 'brown_stained_glass_pane', 'green_stained_glass_pane',
    'red_stained_glass_pane', 'black_stained_glass_pane', 'acacia_leaves', 'dark_oak_leaves', 'acacia_log', 'dark_oak_log', 'acacia_stairs', 'dark_oak_stairs',
    'slime_block', 'barrier', 'iron_trapdoor', 'prismarine', 'prismarine_bricks', 'dark_prismarine', 'sea_lantern', 'hay_bale',
    'white_carpet', 'orange_carpet', 'magenta_carpet', 'light_blue_carpet', 'yellow_carpet', 'lime_carpet', 'pink_carpet', 'gray_carpet',
    'light_gray_carpet', 'cyan_carpet', 'purple_carpet', 'blue_carpet', 'brown_carpet', 'green_carpet', 'red_carpet', 'black_carpet',
    'terracotta', 'coal_block', 'packed_ice', 'sunflower', 'lilac', 'tall_grass', 'large_fern', 'rose_bush',
    'peony', 'red_sandstone', 'chiseled_red_sandstone', 'smooth_red_sandstone', 'red_sandstone_stairs', 'red_sandstone_slab', 'spruce_fence_gate', 'birch_fence_gate',
    'jungle_fence_gate', 'dark_oak_fence_gate', 'acacia_fence_gate', 'spruce_fence', 'birch_fence', 'jungle_fence', 'dark_oak_fence', 'acacia_fence',
    'apple', 'arrow', 'coal', 'charcoal', 'diamond', 'iron_ingot', 'gold_ingot', 'stick',
    'bowl', 'mushroom_stew', 'string', 'feather', 'gunpowder', 'seeds', 'wheat', 'bread',
    'flint', 'raw_porkchop', 'cooked_porkchop', 'painting', 'golden_apple', 'enchanted_golden_apple', 'oak_sign', 'oak_door',
    'bucket', 'water_bucket', 'lava_bucket', 'minecart', 'saddle', 'iron_door', 'redstone_dust', 'snowball',
    'oak_boat', 'leather', 'milk_bucket', 'brick', 'clay_ball', 'sugar_canes', 'paper', 'book',
    'slimeball', 'minecart_with_chest', 'minecart_with_furnace', 'egg', 'compass', 'clock', 'glowstone_dust', 'raw_fish',
    'raw_salmon', 'clownfish', 'pufferfish', 'cooked_fish', 'cooked_salmon', 'ink_sac', 'red_dye', 'green_dye',
    'cocoa_beans', 'lapis_lazuli', 'purple_dye', 'cyan_dye', 'light_gray_dye', 'gray_dye', 'pink_dye', 'lime_dye',
    'yellow_dye', 'light_blue_dye', 'magenta_dye', 'orange_dye', 'bone_meal', 'bone', 'sugar', 'cake',
    'red_bed', 'redstone_repeater', 'cookie', 'filled_map', 'melon_slice', 'pumpkin_seeds', 'melon_seeds', 'raw_beef',
    'steak', 'raw_chicken', 'cooked_chicken', 'rotten_flesh', 'ender_pearl', 'blaze_rod', 'ghast_tear', 'gold_nugget',
    'nether_wart', 'water_bottle', 'potion_of_regeneration', 'potion_of_swiftness', 'potion_of_poison', 'potion_of_strength', 'potion_of_leaping', 'potion_of_regeneration_2',
    'potion_of_swiftness_2', 'potion_of_fire_resistance', 'potion_of_poison_2', 'potion_of_healing', 'potion_of_night_vision', 'potion_of_weakness', 'potion_of_strength_2', 'potion_of_slowness',
    'potion_of_leaping_2', 'potion_of_harming', 'potion_of_water_breathing', 'potion_of_invisibility', 'potion_of_regeneration_long', 'potion_of_swiftness_long', 'potion_of_fire_resistance_long', 'potion_of_poison_long',
    'potion_of_healing_long', 'potion_of_night_vision_long', 'potion_of_weakness_long', 'potion_of_strength_long', 'potion_of_slowness_long', 'potion_of_leaping_long', 'potion_of_harming_long', 'potion_of_water_breathing_long',
    'potion_of_invisibility_long', 'splash_potion_of_regeneration', 'splash_potion_of_swiftness', 'splash_potion_of_poison', 'splash_potion_of_strength', 'splash_potion_of_leaping', 'splash_potion_of_regeneration_2', 'splash_potion_of_swiftness_2',
    'splash_potion_of_fire_resistance', 'splash_potion_of_poison_2', 'splash_potion_of_healing', 'splash_potion_of_night_vision', 'splash_potion_of_weakness', 'splash_potion_of_strength_2', 'splash_potion_of_slowness', 'splash_potion_of_leaping_2',
    'splash_potion_of_harming', 'splash_potion_of_water_breathing', 'splash_potion_of_invisibility', 'splash_potion_of_regeneration_long', 'splash_potion_of_swiftness_long', 'splash_potion_of_fire_resistance_long', 'splash_potion_of_poison_long', 'splash_potion_of_healing_long',
    'splash_potion_of_night_vision_long', 'splash_potion_of_weakness_long', 'splash_potion_of_strength_long', 'splash_potion_of_slowness_long', 'splash_potion_of_leaping_long', 'splash_potion_of_harming_long', 'splash_potion_of_water_breathing_long', 'splash_potion_of_invisibility_long',
    'glass_bottle', 'spider_eye', 'fermented_spider_eye', 'blaze_powder', 'magma_cream', 'brewing_stand', 'cauldron', 'eye_of_ender',
    'glistering_melon_slice', 'creeper_spawn_egg', 'skeleton_spawn_egg', 'spider_spawn_egg', 'zombie_spawn_egg', 'slime_spawn_egg', 'ghast_spawn_egg', 'zombified_piglin_spawn_egg',
    'enderman_spawn_egg', 'cave_spider_spawn_egg', 'silverfish_spawn_egg', 'blaze_spawn_egg', 'magma_cube_spawn_egg', 'bat_spawn_egg', 'witch_spawn_egg', 'endermite_spawn_egg',
    'guardian_spawn_egg', 'pig_spawn_egg', 'sheep_spawn_egg', 'cow_spawn_egg', 'chicken_spawn_egg', 'squid_spawn_egg', 'wolf_spawn_egg', 'mooshroom_spawn_egg',
    'ocelot_spawn_egg', 'horse_spawn_egg', 'rabbit_spawn_egg', 'villager_spawn_egg', 'bottle_o_enchanting', 'fire_charge', 'book_and_quill', 'written_book',
    'emerald', 'item_frame', 'flower_pot', 'carrot', 'potato', 'baked_potato', 'poisonous_potato', 'map',
    'golden_carrot', 'skeleton_skull', 'wither_skeleton_skull', 'zombie_head', 'player_head', 'creeper_head', 'nether_star', 'pumpkin_pie',
    'firework_rocket', 'firework_star', 'enchanted_book', 'redstone_comparator', 'nether_brick', 'nether_quartz', 'minecart_with_tnt', 'minecart_with_hopper',
    'prismarine_shard', 'prismarine_crystals', 'raw_rabbit', 'cooked_rabbit', 'rabbit_stew', 'rabbits_foot', 'rabbit_hide', 'armor_stand',
    'iron_horse_armor', 'gold_horse_armor', 'diamond_horse_armor', 'lead', 'name_tag', 'minecart_with_command_block', 'raw_mutton', 'cooked_mutton',
    'black_banner', 'red_banner', 'green_banner', 'brown_banner', 'blue_banner', 'purple_banner', 'cyan_banner', 'light_gray_banner',
    'gray_banner', 'pink_banner', 'lime_banner', 'yellow_banner', 'light_blue_banner', 'magenta_banner', 'orange_banner', 'white_banner',
    'spruce_door', 'birch_door', 'jungle_door', 'acacia_door', 'dark_oak_door', 'music_disc_13', 'music_disc_cat', 'music_disc_blocks',
    'music_disc_chirp', 'music_disc_far', 'music_disc_mall', 'music_disc_mellohi', 'music_disc_stal', 'music_disc_strad', 'music_disc_ward', 'music_disc_11',
    'music_disc_wait',
]
DAMAGEABLE_ITEM_KEYS = Literal[
    'iron_shovel', 'iron_pickaxe', 'iron_axe', 'flint_and_steel', 'bow', 'iron_sword', 'wooden_sword', 'wooden_shovel',
    'wooden_pickaxe', 'wooden_axe', 'stone_sword', 'stone_shovel', 'stone_pickaxe', 'stone_axe', 'diamond_sword', 'diamond_shovel',
    'diamond_pickaxe', 'diamond_axe', 'golden_sword', 'golden_shovel', 'golden_pickaxe', 'golden_axe', 'wooden_hoe', 'stone_hoe',
    'iron_hoe', 'diamond_hoe', 'golden_hoe', 'chain_helmet', 'chain_chestplate', 'chain_leggings', 'chain_boots', 'iron_helmet',
    'iron_chestplate', 'iron_leggings', 'iron_boots', 'diamond_helmet', 'diamond_chestplate', 'diamond_leggings', 'diamond_boots', 'golden_helmet',
    'golden_chestplate', 'golden_leggings', 'golden_boots', 'fishing_rod', 'shears', 'carrot_on_a_stick',
]
LEATHER_ARMOR_KEYS = Literal[
    'leather_cap', 'leather_tunic', 'leather_pants', 'leather_boots',
]
ALL_POSSIBLE_ITEM_KEYS = NON_SPECIAL_ITEM_KEYS | DAMAGEABLE_ITEM_KEYS | LEATHER_ARMOR_KEYS


EnchantmentsType = dict[Enchantment | ALL_POSSIBLE_ENCHANTMENTS, int] | Iterable[Enchantment | ALL_POSSIBLE_ENCHANTMENTS] | Enchantment | ALL_POSSIBLE_ENCHANTMENTS


SAVED_CACHE: dict[str, str] = {}


class Item:
    key: str
    extras: dict[str, Any]

    @overload
    def __init__(
        self,
        key: NON_SPECIAL_ITEM_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str | Iterable[str]] = None,
        count: int = 1,
        enchantments: Optional[EnchantmentsType] = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        key: DAMAGEABLE_ITEM_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str | Iterable[str]] = None,
        count: int = 1,
        enchantments: Optional[EnchantmentsType] = None,
        unbreakable: bool = False,
        damage: int = 0,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_unbreakable_flag: bool = False,
        hide_additional_flag: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        key: LEATHER_ARMOR_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str | Iterable[str]] = None,
        count: int = 1,
        enchantments: Optional[EnchantmentsType] = None,
        unbreakable: bool = False,
        damage: int = 0,
        color: int | str | tuple[int, int, int] = 0,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_unbreakable_flag: bool = False,
        hide_additional_flag: bool = False,
        hide_dye_flag: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        key: ALL_POSSIBLE_ITEM_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str | Iterable[str]] = None,
        count: int = 1,
        enchantments: Optional[EnchantmentsType] = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
        **extras: Any,
    ) -> None:
        ...

    def __init__(
        self,
        key: ALL_POSSIBLE_ITEM_KEYS,
        **extras: Any,
    ) -> None:
        self.key = key
        self.extras = extras
        self.key_check()

    def as_title(self) -> str:
        return self.key_check()['title']

    def replace_placeholders(self, text: str) -> str:
        return re.sub(r'&([0-9a-fk-or])', r'§\1', text)

    def one_lineify(
        self,
        data: dict[
            str, tuple[int | str | list[int] | list[str] | list[dict[str, int]], DataType] | dict[
                str, tuple[int | str | list[int] | list[str] | list[dict[str, int]], DataType] | dict[
                    str, tuple[int | str | list[int] | list[str] | list[dict[str, int]], DataType]
                ]
            ]
        ] | tuple[int | str | list[int] | list[str] | list[dict[str, int]], DataType],
    ) -> str:
        if isinstance(data, tuple):
            left, right = data
            if isinstance(left, (int, str)):
                return right.value(left)
            else:
                inside = type(left[0])
                if inside is dict:
                    mappings: list[dict[str, int]] = left  # type: ignore
                    return '[' + ','.join(f'{i}:{{' + ','.join(f'{k}:{right.value(v)}' for k, v in item.items()) + '}' for i, item in enumerate(mappings)) + ']'
                else:
                    return '[' + ','.join(f'{i}:{right.value(x)}' for i, x in enumerate(left)) + ']'
        return '{' + ','.join(f'{k}:{self.one_lineify(v)}' for k, v in data.items()) + '}'  # type: ignore

    def fetch_line(self, item: ItemJsonData) -> str:
        extras_copy = self.extras.copy()
        # cant be arsed to annotate the following because look at `one_lineify`
        data = {
            'id': (item['name'], DataType.string),
            'Count': (extras_copy.pop('count', 1), DataType.byte),
            'tag': {},
            'Damage': (item['data_value'], DataType.short),
        }
        if item['can_be_damaged']:
            data['Damage'] = (extras_copy.pop('damage', 0), DataType.short)
        tags = data['tag']

        enchantments: Optional[EnchantmentsType] = extras_copy.pop('enchantments', None)
        if enchantments is not None:
            if isinstance(enchantments, str):
                enchantments = Enchantment(enchantments)
            if isinstance(enchantments, Enchantment):
                enchantments = [enchantments]
            if isinstance(enchantments, dict):
                tags['ench'] = ([{
                    'lvl': value,
                    'id': ENCHANTMENT_TO_ID[key if isinstance(key, str) else key.name],
                } for key, value in enchantments.items()], DataType.short)
            else:
                tags['ench'] = ([{
                    'lvl': 1 if isinstance(enchantment, str) else enchantment.level or 1,
                    'id': ENCHANTMENT_TO_ID[enchantment if isinstance(enchantment, str) else enchantment.name],
                } for enchantment in enchantments], DataType.short)

        unbreakable: int = int(extras_copy.pop('unbreakable', False))
        if unbreakable:
            if not item['can_be_damaged']:
                raise ValueError(f'Item "{self.key}" cannot be unbreakable.')
            tags['Unbreakable'] = (1, DataType.byte)

        hide_flags: int = min(sum(
            value for key, value in HIDE_FLAGS.items() if extras_copy.pop(key, False)
        ), HIDE_FLAGS['hide_all_flags'])
        if hide_flags:
            tags['HideFlags'] = (hide_flags, DataType.integer)

        lore: Optional[str | Iterable[str]] = extras_copy.pop('lore', None)
        if lore is not None:
            if not isinstance(lore, str):
                lore = '\n'.join(lore)
            if lore:
                lore = self.replace_placeholders(lore)
                display = tags.setdefault('display', {})
                display['Lore'] = (lore.split('\n'), DataType.string)

        name: Optional[str] = extras_copy.pop('name', None)
        if name is not None:
            name = self.replace_placeholders(name)
            display = tags.setdefault('display', {})
            display['Name'] = (name, DataType.string)

        if not tags:
            del data['tag']

        if extras_copy:
            raise ValueError(f'Invalid keys: {", ".join(extras_copy.keys())}')

        return '{"item": "' + self.one_lineify(data) + '"}'

    def key_check(self) -> ItemJsonData:
        item = ITEMS.get(self.key, None)
        if item is None:
            closest = difflib.get_close_matches(self.key.lower(), ITEMS.keys(), n=1, cutoff=0.0)[0]
            raise ValueError(
                f'Invalid item key: \x1b[38;2;255;0;0m{self.key}\x1b[0m. Did you mean \x1b[38;2;0;255;0m{closest}\x1b[0m?\nYou\'ve already saved this in your imports folder? Do not create an Item, use the string "{self.key}" instead.'
            )
        return item

    def save(self) -> str:
        item = self.key_check()
        line = self.fetch_line(item)
        cached = SAVED_CACHE.get(line, None)
        if cached is not None:
            print(f'Using cached \x1b[38;2;0;255;0m{item["title"]}\x1b[0m as \x1b[38;2;255;0;0m{cached}\x1b[0m.')
            return cached
        suffix = hashlib.md5(line.encode()).hexdigest()[:8]
        name = f'_{self.key}_{suffix}'
        path = HTSL_IMPORTS_FOLDER / f'{name}.json'
        with path.open('w', encoding='utf-8') as file:
            file.write(line)
        SAVED_CACHE[line] = name
        print(f'Successfully saved \x1b[38;2;0;255;0m{item["title"]}\x1b[0m as \x1b[38;2;255;0;0m{name}\x1b[0m to be used in your script. Written it to\n{path.absolute()}')
        return name
