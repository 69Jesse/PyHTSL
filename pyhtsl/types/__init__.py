from ..condition.base_condition import BaseCondition
from ..condition.conditional_statements import IfStatement
from ..expression.assignment_expression import Expression

from typing import Literal


__all__ = (
    'BaseCondition',
    'IfStatement',
    'Expression',
    'ALL_POTION_EFFECTS',
    'ALL_DAMAGE_CAUSES',
    'ALL_ENCHANTMENTS',
    'ENCHANTMENT_TO_ID',
    'INVENTORY_SLOTS',
    '_INVENTORY_SLOTS_PRETTY_NAME_MAPPING',
    'NON_SPECIAL_ITEM_KEYS',
    'DAMAGEABLE_ITEM_KEYS',
    'LEATHER_ARMOR_KEYS',
    'ALL_ITEM_KEYS',
    'ALL_LOCATIONS',
    'ALL_SOUNDS_PRETTY',
    'ALL_SOUNDS_RAW',
    'ALL_SOUNDS_PRETTY_TO_RAW',
    'ALL_LOCATIONS',
)


ALL_POTION_EFFECTS = Literal[
    'speed',
    'slowness',
    'haste',
    'mining_fatigue',
    'strength',
    'instant_health',
    'instant_damage',
    'jump_boost',
    'nausea',
    'regeneration',
    'resistance',
    'fire_resistance',
    'water_breathing',
    'invisibility',
    'blindness',
    'night_vision',
    'hunger',
    'weakness',
    'poison',
    'wither',
    'health_boost',
    'absorption',
]


ALL_DAMAGE_CAUSES = Literal[
    'entity_attack',
    'projectile',
    'suffocation',
    'fall',
    'lava',
    'fire',
    'fire_tick',
    'drowning',
    'starvation',
    'poison',
    'thorns',
]


ALL_ENCHANTMENTS = Literal[
    'protection',
    'fire_protection',
    'feather_falling',
    'blast_protection',
    'projectile_protection',
    'respiration',
    'aqua_affinity',
    'thorns',
    'depth_strider',
    'sharpness',
    'smite',
    'bane_of_arthropods',
    'knockback',
    'fire_aspect',
    'looting',
    'efficiency',
    'silk_touch',
    'unbreaking',
    'fortune',
    'power',
    'punch',
    'flame',
    'infinity',
    'luck_of_the_sea',
    'lure',
]


ENCHANTMENT_TO_ID: dict[ALL_ENCHANTMENTS, int] = {
    'protection': 0,
    'fire_protection': 1,
    'feather_falling': 2,
    'blast_protection': 3,
    'projectile_protection': 4,
    'respiration': 5,
    'aqua_affinity': 6,
    'thorns': 7,
    'depth_strider': 8,
    'sharpness': 16,
    'smite': 17,
    'bane_of_arthropods': 18,
    'knockback': 19,
    'fire_aspect': 20,
    'looting': 21,
    'efficiency': 32,
    'silk_touch': 33,
    'unbreaking': 34,
    'fortune': 35,
    'power': 48,
    'punch': 49,
    'flame': 50,
    'infinity': 51,
    'luck_of_the_sea': 61,
    'lure': 62,
}


INVENTORY_SLOTS = Literal[
    'hand_slot', 'Hand Slot', -2,
    'first_slot', 'First Slot', 'First Available Slot', -1,
    'hotbar_slot_1', 'Hotbar Slot 1', 0,
    'hotbar_slot_2', 'Hotbar Slot 2', 1,
    'hotbar_slot_3', 'Hotbar Slot 3', 2,
    'hotbar_slot_4', 'Hotbar Slot 4', 3,
    'hotbar_slot_5', 'Hotbar Slot 5', 4,
    'hotbar_slot_6', 'Hotbar Slot 6', 5,
    'hotbar_slot_7', 'Hotbar Slot 7', 6,
    'hotbar_slot_8', 'Hotbar Slot 8', 7,
    'hotbar_slot_9', 'Hotbar Slot 9', 8,
    'inventory_slot_1', 'Inventory Slot 1', 9,
    'inventory_slot_2', 'Inventory Slot 2', 10,
    'inventory_slot_3', 'Inventory Slot 3', 11,
    'inventory_slot_4', 'Inventory Slot 4', 12,
    'inventory_slot_5', 'Inventory Slot 5', 13,
    'inventory_slot_6', 'Inventory Slot 6', 14,
    'inventory_slot_7', 'Inventory Slot 7', 15,
    'inventory_slot_8', 'Inventory Slot 8', 16,
    'inventory_slot_9', 'Inventory Slot 9', 17,
    'inventory_slot_10', 'Inventory Slot 10', 18,
    'inventory_slot_11', 'Inventory Slot 11', 19,
    'inventory_slot_12', 'Inventory Slot 12', 20,
    'inventory_slot_13', 'Inventory Slot 13', 21,
    'inventory_slot_14', 'Inventory Slot 14', 22,
    'inventory_slot_15', 'Inventory Slot 15', 23,
    'inventory_slot_16', 'Inventory Slot 16', 24,
    'inventory_slot_17', 'Inventory Slot 17', 25,
    'inventory_slot_18', 'Inventory Slot 18', 26,
    'inventory_slot_19', 'Inventory Slot 19', 27,
    'inventory_slot_20', 'Inventory Slot 20', 28,
    'inventory_slot_21', 'Inventory Slot 21', 29,
    'inventory_slot_22', 'Inventory Slot 22', 30,
    'inventory_slot_23', 'Inventory Slot 23', 31,
    'inventory_slot_24', 'Inventory Slot 24', 32,
    'inventory_slot_25', 'Inventory Slot 25', 33,
    'inventory_slot_26', 'Inventory Slot 26', 34,
    'inventory_slot_27', 'Inventory Slot 27', 35,
    'boots', 'Boots', 36,
    'leggings', 'Leggings', 37,
    'chestplate', 'Chestplate', 38,
    'helmet', 'Helmet', 39,
]


# HTSL only seems to accept the pretty names for inventory slots
_INVENTORY_SLOTS_PRETTY_NAME_MAPPING: dict[INVENTORY_SLOTS, INVENTORY_SLOTS] = {
    'hand_slot': -2,
    'Hand Slot': -2,
    'first_slot': -1,
    'First Slot': -1,
    'First Available Slot': -1,
    'hotbar_slot_1': 0,
    'Hotbar Slot 1': 0,
    'hotbar_slot_2': 1,
    'Hotbar Slot 2': 1,
    'hotbar_slot_3': 2,
    'Hotbar Slot 3': 2,
    'hotbar_slot_4': 3,
    'Hotbar Slot 4': 3,
    'hotbar_slot_5': 4,
    'Hotbar Slot 5': 4,
    'hotbar_slot_6': 5,
    'Hotbar Slot 6': 5,
    'hotbar_slot_7': 6,
    'Hotbar Slot 7': 6,
    'hotbar_slot_8': 7,
    'Hotbar Slot 8': 7,
    'hotbar_slot_9': 8,
    'Hotbar Slot 9': 8,
    'inventory_slot_1': 9,
    'Inventory Slot 1': 9,
    'inventory_slot_2': 10,
    'Inventory Slot 2': 10,
    'inventory_slot_3': 11,
    'Inventory Slot 3': 11,
    'inventory_slot_4': 12,
    'Inventory Slot 4': 12,
    'inventory_slot_5': 13,
    'Inventory Slot 5': 13,
    'inventory_slot_6': 14,
    'Inventory Slot 6': 14,
    'inventory_slot_7': 15,
    'Inventory Slot 7': 15,
    'inventory_slot_8': 16,
    'Inventory Slot 8': 16,
    'inventory_slot_9': 17,
    'Inventory Slot 9': 17,
    'inventory_slot_10': 18,
    'Inventory Slot 10': 18,
    'inventory_slot_11': 19,
    'Inventory Slot 11': 19,
    'inventory_slot_12': 20,
    'Inventory Slot 12': 20,
    'inventory_slot_13': 21,
    'Inventory Slot 13': 21,
    'inventory_slot_14': 22,
    'Inventory Slot 14': 22,
    'inventory_slot_15': 23,
    'Inventory Slot 15': 23,
    'inventory_slot_16': 24,
    'Inventory Slot 16': 24,
    'inventory_slot_17': 25,
    'Inventory Slot 17': 25,
    'inventory_slot_18': 26,
    'Inventory Slot 18': 26,
    'inventory_slot_19': 27,
    'Inventory Slot 19': 27,
    'inventory_slot_20': 28,
    'Inventory Slot 20': 28,
    'inventory_slot_21': 29,
    'Inventory Slot 21': 29,
    'inventory_slot_22': 30,
    'Inventory Slot 22': 30,
    'inventory_slot_23': 31,
    'Inventory Slot 23': 31,
    'inventory_slot_24': 32,
    'Inventory Slot 24': 32,
    'inventory_slot_25': 33,
    'Inventory Slot 25': 33,
    'inventory_slot_26': 34,
    'Inventory Slot 26': 34,
    'inventory_slot_27': 35,
    'Inventory Slot 27': 35,
    'boots': 36,
    'Boots': 36,
    'leggings': 37,
    'Leggings': 37,
    'chestplate': 38,
    'Chestplate': 38,
    'helmet': 39,
    'Helmet': 39,
}


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
    'activator_rails', 'dropper', 'white_stained_clay', 'orange_stained_clay', 'magenta_stained_clay', 'light_blue_stained_clay', 'yellow_stained_clay', 'lime_stained_clay',
    'pink_stained_clay', 'gray_stained_clay', 'light_gray_stained_clay', 'cyan_stained_clay', 'purple_stained_clay', 'blue_stained_clay', 'brown_stained_clay', 'green_stained_clay',
    'red_stained_clay', 'black_stained_clay', 'white_stained_glass_pane', 'orange_stained_glass_pane', 'magenta_stained_glass_pane', 'light_blue_stained_glass_pane', 'yellow_stained_glass_pane', 'lime_stained_glass_pane',
    'pink_stained_glass_pane', 'gray_stained_glass_pane', 'light_gray_stained_glass_pane', 'cyan_stained_glass_pane', 'purple_stained_glass_pane', 'blue_stained_glass_pane', 'brown_stained_glass_pane', 'green_stained_glass_pane',
    'red_stained_glass_pane', 'black_stained_glass_pane', 'acacia_leaves', 'dark_oak_leaves', 'acacia_log', 'dark_oak_log', 'acacia_stairs', 'dark_oak_stairs',
    'slime_block', 'barrier', 'iron_trapdoor', 'prismarine', 'prismarine_bricks', 'dark_prismarine', 'sea_lantern', 'hay_bale',
    'white_carpet', 'orange_carpet', 'magenta_carpet', 'light_blue_carpet', 'yellow_carpet', 'lime_carpet', 'pink_carpet', 'gray_carpet',
    'light_gray_carpet', 'cyan_carpet', 'purple_carpet', 'blue_carpet', 'brown_carpet', 'green_carpet', 'red_carpet', 'black_carpet',
    'stained_clay', 'coal_block', 'packed_ice', 'sunflower', 'lilac', 'tall_grass', 'large_fern', 'rose_bush',
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
    'red_bed', 'redstone_repeater', 'filled_map', 'melon_slice', 'pumpkin_seeds', 'melon_seeds', 'raw_beef',
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
    'golden_carrot', 'skeleton_skull', 'wither_skeleton_skull', 'zombie_head', 'creeper_head', 'nether_star', 'pumpkin_pie',
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


COOKIE_ITEM_KEY = Literal['cookie']


PLAYER_SKULL_ITEM_KEY = Literal['player_head']


ALL_ITEM_KEYS = NON_SPECIAL_ITEM_KEYS | DAMAGEABLE_ITEM_KEYS | LEATHER_ARMOR_KEYS | COOKIE_ITEM_KEY | PLAYER_SKULL_ITEM_KEY


ALL_LOCATIONS = Literal[
    'house_spawn',
    'current_location',
    'invokers_location',
    'custom_coordinates',
]


ALL_SOUNDS_PRETTY = Literal[
    'Ambience Cave', 'Ambience Rain', 'Ambience Thunder', 'Anvil Break', 'Anvil Land', 'Anvil Use', 'Arrow Hit', 'Burp',
    'Chest Close', 'Chest Open', 'Click', 'Door Close', 'Door Open', 'Drink', 'Eat', 'Explode',
    'Fall Big', 'Fall Small', 'Fizz', 'Fuse', 'Glass', 'Hurt Flesh', 'Item Break', 'Item Pickup',
    'Lava Pop', 'Level Up', 'Note Bass', 'Note Piano', 'Note Bass Drum', 'Note Sticks', 'Note Bass Guitar', 'Note Snare Drum',
    'Note Pling', 'Orb Pickup', 'Shoot Arrow', 'Splash', 'Swim', 'Wood Click', 'Bat Death', 'Bat Hurt',
    'Bat Idle', 'Bat Loop', 'Bat Takeoff', 'Blaze Breath', 'Blaze Death', 'Blaze Hit', 'Cat Hiss', 'Cat Hit',
    'Cat Meow', 'Cat Purr', 'Cat Purreow', 'Chicken Idle', 'Chicken Hurt', 'Chicken Egg Pop', 'Chicken Walk', 'Cow Idle',
    'Cow Hurt', 'Cow Walk', 'Creeper Hiss', 'Creeper Death', 'Enderdragon Death', 'Enderdragon Growl', 'Enderdragon Hit', 'Enderdragon Wings',
    'Enderman Death', 'Enderman Hit', 'Enderman Idle', 'Enderman Teleport', 'Enderman Scream', 'Enderman Stare', 'Ghast Scream', 'Ghast Scream2',
    'Ghast Charge', 'Ghast Death', 'Ghast Fireball', 'Ghast Moan', 'Guardian Hit', 'Guardian Idle', 'Guardian Death', 'Guardian Elder Hit',
    'Guardian Elder Idle', 'Guardian Elder Death', 'Guardian Land Hit', 'Guardian Land Idle', 'Guardian Land Death', 'Guardian Curse', 'Guardian Attack', 'Guardian Flop',
    'Irongolem Death', 'Irongolem Hit', 'Irongolem Throw', 'Irongolem Walk', 'Magmacube Walk', 'Magmacube Walk2', 'Magmacube Jump', 'Pig Idle',
    'Pig Death', 'Pig Walk', 'Rabbit Ambient', 'Rabbit Death', 'Rabbit Hurt', 'Rabbit Jump', 'Sheep Idle', 'Sheep Shear',
    'Sheep Walk', 'Silverfish Hit', 'Silverfish Kill', 'Silverfish Idle', 'Silverfish Walk', 'Skeleton Idle', 'Skeleton Death', 'Skeleton Hurt',
    'Skeleton Walk', 'Slime Attack', 'Slime Walk', 'Slime Walk2', 'Spider Idle', 'Spider Death', 'Spider Walk', 'Wither Death',
    'Wither Hurt', 'Wither Idle', 'Wither Shoot', 'Wither Spawn', 'Wolf Bark', 'Wolf Death', 'Wolf Growl', 'Wolf Howl',
    'Wolf Hurt', 'Wolf Pant', 'Wolf Shake', 'Wolf Walk', 'Wolf Whine', 'Zombie Metal', 'Zombie Wood', 'Zombie Woodbreak',
    'Zombie Idle', 'Zombie Death', 'Zombie Hurt', 'Zombie Infect', 'Zombie Unfect', 'Zombie Remedy', 'Zombie Walk', 'Zombie Pig Idle',
    'Zombie Pig Angry', 'Zombie Pig Death', 'Zombie Pig Hurt', 'Firework Blast', 'Firework Blast2', 'Firework Large Blast', 'Firework Large Blast2', 'Firework Twinkle',
    'Firework Twinkle2', 'Firework Launch', 'Successful Hit', 'Horse Angry', 'Horse Armor', 'Horse Breathe', 'Horse Death', 'Horse Gallop',
    'Horse Hit', 'Horse Idle', 'Horse Jump', 'Horse Land', 'Horse Saddle', 'Horse Soft', 'Horse Wood', 'Donkey Angry',
    'Donkey Death', 'Donkey Hit', 'Donkey Idle', 'Horse Skeleton Death', 'Horse Skeleton Hit', 'Horse Skeleton Idle', 'Horse Zombie Death', 'Horse Zombie Hit',
    'Horse Zombie Idle', 'Villager Death', 'Villager Haggle', 'Villager Hit', 'Villager Idle', 'Villager No', 'Villager Yes',
]


ALL_SOUNDS_RAW = Literal[
    'ambient.cave.cave', 'ambient.weather.rain', 'ambient.weather.thunder', 'random.anvil_break', 'random.anvil_land', 'random.anvil_use', 'random.bowhit', 'random.burp',
    'random.chestclosed', 'random.chestopen', 'random.click', 'random.door_close', 'random.door_open', 'random.drink', 'random.eat', 'random.explode',
    'game.player.hurt.fall.big', 'game.player.hurt.fall.small', 'random.fizz', 'game.tnt.primed', 'dig.glass', 'game.player.hurt', 'random.break', 'random.pop',
    'liquid.lavapop', 'random.levelup', 'note.bass', 'note.harp', 'note.bd', 'note.hat', 'note.bassattack', 'note.snare',
    'note.pling', 'random.orb', 'random.bow', 'game.player.swim.splash', 'game.player.swim', 'random.wood_click', 'mob.bat.death', 'mob.bat.hurt',
    'mob.bat.idle', 'mob.bat.loop', 'mob.bat.takeoff', 'mob.blaze.breathe', 'mob.blaze.death', 'mob.blaze.hit', 'mob.cat.hiss', 'mob.cat.hitt',
    'mob.cat.meow', 'mob.cat.purr', 'mob.cat.purreow', 'mob.chicken.say', 'mob.chicken.hurt', 'mob.chicken.plop', 'mob.chicken.step', 'mob.cow.say',
    'mob.cow.hurt', 'mob.cow.step', 'mob.creeper.say', 'mob.creeper.death', 'mob.enderdragon.end', 'mob.enderdragon.growl', 'mob.enderdragon.hit', 'mob.enderdragon.wings',
    'mob.endermen.death', 'mob.endermen.hit', 'mob.endermen.idle', 'mob.endermen.portal', 'mob.endermen.scream', 'mob.endermen.stare', 'mob.ghast.scream', 'mob.ghast.affectionate_scream',
    'mob.ghast.charge', 'mob.ghast.death', 'mob.ghast.fireball', 'mob.ghast.moan', 'mob.guardian.hit', 'mob.guardian.idle', 'mob.guardian.death', 'mob.guardian.elder.hit',
    'mob.guardian.elder.idle', 'mob.guardian.elder.death', 'mob.guardian.land.hit', 'mob.guardian.land.idle', 'mob.guardian.land.death', 'mob.guardian.curse', 'mob.guardian.attack', 'mob.guardian.flop',
    'mob.irongolem.death', 'mob.irongolem.hit', 'mob.irongolem.throw', 'mob.irongolem.walk', 'mob.magmacube.small', 'mob.magmacube.big', 'mob.magmacube.jump', 'mob.pig.say',
    'mob.pig.death', 'mob.pig.step', 'mob.rabbit.idle', 'mob.rabbit.death', 'mob.rabbit.hurt', 'mob.rabbit.hop', 'mob.sheep.say', 'mob.sheep.shear',
    'mob.sheep.step', 'mob.silverfish.hit', 'mob.silverfish.kill', 'mob.silverfish.say', 'mob.silverfish.step', 'mob.skeleton.say', 'mob.skeleton.death', 'mob.skeleton.hurt',
    'mob.skeleton.step', 'mob.slime.attack', 'mob.slime.small', 'mob.slime.big', 'mob.spider.say', 'mob.spider.death', 'mob.spider.step', 'mob.wither.death',
    'mob.wither.hurt', 'mob.wither.idle', 'mob.wither.shoot', 'mob.wither.spawn', 'mob.wolf.bark', 'mob.wolf.death', 'mob.wolf.growl', 'mob.wolf.howl',
    'mob.wolf.hurt', 'mob.wolf.panting', 'mob.wolf.shake', 'mob.wolf.step', 'mob.wolf.whine', 'mob.zombie.metal', 'mob.zombie.wood', 'mob.zombie.woodbreak',
    'mob.zombie.say', 'mob.zombie.death', 'mob.zombie.hurt', 'mob.zombie.infect', 'mob.zombie.unfect', 'mob.zombie.remedy', 'mob.zombie.step', 'mob.zombiepig.zpig',
    'mob.zombiepig.zpigangry', 'mob.zombiepig.zpigdeath', 'mob.zombiepig.zpighurt', 'fireworks.blast', 'fireworks.blast_far', 'fireworks.largeBlast', 'fireworks.largeBlast_far', 'fireworks.twinkle',
    'fireworks.twinkle_far', 'fireworks.launch', 'random.successful_hit', 'mob.horse.angry', 'mob.horse.armor', 'mob.horse.breathe', 'mob.horse.death', 'mob.horse.gallop',
    'mob.horse.hit', 'mob.horse.idle', 'mob.horse.jump', 'mob.horse.land', 'mob.horse.leather', 'mob.horse.soft', 'mob.horse.wood', 'mob.horse.donkey.angry',
    'mob.horse.donkey.death', 'mob.horse.donkey.hit', 'mob.horse.donkey.idle', 'mob.horse.skeleton.death', 'mob.horse.skeleton.hit', 'mob.horse.skeleton.idle', 'mob.horse.zombie.death', 'mob.horse.zombie.hit',
    'mob.horse.zombie.idle', 'mob.villager.death', 'mob.villager.haggle', 'mob.villager.hit', 'mob.villager.idle', 'mob.villager.no', 'mob.villager.yes',
]


ALL_SOUNDS_PRETTY_TO_RAW = {
    'Ambience Cave': 'ambient.cave.cave', 'Ambience Rain': 'ambient.weather.rain', 'Ambience Thunder': 'ambient.weather.thunder', 'Anvil Break': 'random.anvil_break',
    'Anvil Land': 'random.anvil_land', 'Anvil Use': 'random.anvil_use', 'Arrow Hit': 'random.bowhit', 'Burp': 'random.burp',
    'Chest Close': 'random.chestclosed', 'Chest Open': 'random.chestopen', 'Click': 'random.click', 'Door Close': 'random.door_close',
    'Door Open': 'random.door_open', 'Drink': 'random.drink', 'Eat': 'random.eat', 'Explode': 'random.explode',
    'Fall Big': 'game.player.hurt.fall.big', 'Fall Small': 'game.player.hurt.fall.small', 'Fizz': 'random.fizz', 'Fuse': 'game.tnt.primed',
    'Glass': 'dig.glass', 'Hurt Flesh': 'game.player.hurt', 'Item Break': 'random.break', 'Item Pickup': 'random.pop',
    'Lava Pop': 'liquid.lavapop', 'Level Up': 'random.levelup', 'Note Bass': 'note.bass', 'Note Piano': 'note.harp',
    'Note Bass Drum': 'note.bd', 'Note Sticks': 'note.hat', 'Note Bass Guitar': 'note.bassattack', 'Note Snare Drum': 'note.snare',
    'Note Pling': 'note.pling', 'Orb Pickup': 'random.orb', 'Shoot Arrow': 'random.bow', 'Splash': 'game.player.swim.splash',
    'Swim': 'game.player.swim', 'Wood Click': 'random.wood_click', 'Bat Death': 'mob.bat.death', 'Bat Hurt': 'mob.bat.hurt',
    'Bat Idle': 'mob.bat.idle', 'Bat Loop': 'mob.bat.loop', 'Bat Takeoff': 'mob.bat.takeoff', 'Blaze Breath': 'mob.blaze.breathe',
    'Blaze Death': 'mob.blaze.death', 'Blaze Hit': 'mob.blaze.hit', 'Cat Hiss': 'mob.cat.hiss', 'Cat Hit': 'mob.cat.hitt',
    'Cat Meow': 'mob.cat.meow', 'Cat Purr': 'mob.cat.purr', 'Cat Purreow': 'mob.cat.purreow', 'Chicken Idle': 'mob.chicken.say',
    'Chicken Hurt': 'mob.chicken.hurt', 'Chicken Egg Pop': 'mob.chicken.plop', 'Chicken Walk': 'mob.chicken.step', 'Cow Idle': 'mob.cow.say',
    'Cow Hurt': 'mob.cow.hurt', 'Cow Walk': 'mob.cow.step', 'Creeper Hiss': 'mob.creeper.say', 'Creeper Death': 'mob.creeper.death',
    'Enderdragon Death': 'mob.enderdragon.end', 'Enderdragon Growl': 'mob.enderdragon.growl', 'Enderdragon Hit': 'mob.enderdragon.hit', 'Enderdragon Wings': 'mob.enderdragon.wings',
    'Enderman Death': 'mob.endermen.death', 'Enderman Hit': 'mob.endermen.hit', 'Enderman Idle': 'mob.endermen.idle', 'Enderman Teleport': 'mob.endermen.portal',
    'Enderman Scream': 'mob.endermen.scream', 'Enderman Stare': 'mob.endermen.stare', 'Ghast Scream': 'mob.ghast.scream', 'Ghast Scream2': 'mob.ghast.affectionate_scream',
    'Ghast Charge': 'mob.ghast.charge', 'Ghast Death': 'mob.ghast.death', 'Ghast Fireball': 'mob.ghast.fireball', 'Ghast Moan': 'mob.ghast.moan',
    'Guardian Hit': 'mob.guardian.hit', 'Guardian Idle': 'mob.guardian.idle', 'Guardian Death': 'mob.guardian.death', 'Guardian Elder Hit': 'mob.guardian.elder.hit',
    'Guardian Elder Idle': 'mob.guardian.elder.idle', 'Guardian Elder Death': 'mob.guardian.elder.death', 'Guardian Land Hit': 'mob.guardian.land.hit', 'Guardian Land Idle': 'mob.guardian.land.idle',
    'Guardian Land Death': 'mob.guardian.land.death', 'Guardian Curse': 'mob.guardian.curse', 'Guardian Attack': 'mob.guardian.attack', 'Guardian Flop': 'mob.guardian.flop',
    'Irongolem Death': 'mob.irongolem.death', 'Irongolem Hit': 'mob.irongolem.hit', 'Irongolem Throw': 'mob.irongolem.throw', 'Irongolem Walk': 'mob.irongolem.walk',
    'Magmacube Walk': 'mob.magmacube.small', 'Magmacube Walk2': 'mob.magmacube.big', 'Magmacube Jump': 'mob.magmacube.jump', 'Pig Idle': 'mob.pig.say',
    'Pig Death': 'mob.pig.death', 'Pig Walk': 'mob.pig.step', 'Rabbit Ambient': 'mob.rabbit.idle', 'Rabbit Death': 'mob.rabbit.death',
    'Rabbit Hurt': 'mob.rabbit.hurt', 'Rabbit Jump': 'mob.rabbit.hop', 'Sheep Idle': 'mob.sheep.say', 'Sheep Shear': 'mob.sheep.shear',
    'Sheep Walk': 'mob.sheep.step', 'Silverfish Hit': 'mob.silverfish.hit', 'Silverfish Kill': 'mob.silverfish.kill', 'Silverfish Idle': 'mob.silverfish.say',
    'Silverfish Walk': 'mob.silverfish.step', 'Skeleton Idle': 'mob.skeleton.say', 'Skeleton Death': 'mob.skeleton.death', 'Skeleton Hurt': 'mob.skeleton.hurt',
    'Skeleton Walk': 'mob.skeleton.step', 'Slime Attack': 'mob.slime.attack', 'Slime Walk': 'mob.slime.small', 'Slime Walk2': 'mob.slime.big',
    'Spider Idle': 'mob.spider.say', 'Spider Death': 'mob.spider.death', 'Spider Walk': 'mob.spider.step', 'Wither Death': 'mob.wither.death',
    'Wither Hurt': 'mob.wither.hurt', 'Wither Idle': 'mob.wither.idle', 'Wither Shoot': 'mob.wither.shoot', 'Wither Spawn': 'mob.wither.spawn',
    'Wolf Bark': 'mob.wolf.bark', 'Wolf Death': 'mob.wolf.death', 'Wolf Growl': 'mob.wolf.growl', 'Wolf Howl': 'mob.wolf.howl',
    'Wolf Hurt': 'mob.wolf.hurt', 'Wolf Pant': 'mob.wolf.panting', 'Wolf Shake': 'mob.wolf.shake', 'Wolf Walk': 'mob.wolf.step',
    'Wolf Whine': 'mob.wolf.whine', 'Zombie Metal': 'mob.zombie.metal', 'Zombie Wood': 'mob.zombie.wood', 'Zombie Woodbreak': 'mob.zombie.woodbreak',
    'Zombie Idle': 'mob.zombie.say', 'Zombie Death': 'mob.zombie.death', 'Zombie Hurt': 'mob.zombie.hurt', 'Zombie Infect': 'mob.zombie.infect',
    'Zombie Unfect': 'mob.zombie.unfect', 'Zombie Remedy': 'mob.zombie.remedy', 'Zombie Walk': 'mob.zombie.step', 'Zombie Pig Idle': 'mob.zombiepig.zpig',
    'Zombie Pig Angry': 'mob.zombiepig.zpigangry', 'Zombie Pig Death': 'mob.zombiepig.zpigdeath', 'Zombie Pig Hurt': 'mob.zombiepig.zpighurt', 'Firework Blast': 'fireworks.blast',
    'Firework Blast2': 'fireworks.blast_far', 'Firework Large Blast': 'fireworks.largeBlast', 'Firework Large Blast2': 'fireworks.largeBlast_far', 'Firework Twinkle': 'fireworks.twinkle',
    'Firework Twinkle2': 'fireworks.twinkle_far', 'Firework Launch': 'fireworks.launch', 'Successful Hit': 'random.successful_hit', 'Horse Angry': 'mob.horse.angry',
    'Horse Armor': 'mob.horse.armor', 'Horse Breathe': 'mob.horse.breathe', 'Horse Death': 'mob.horse.death', 'Horse Gallop': 'mob.horse.gallop',
    'Horse Hit': 'mob.horse.hit', 'Horse Idle': 'mob.horse.idle', 'Horse Jump': 'mob.horse.jump', 'Horse Land': 'mob.horse.land',
    'Horse Saddle': 'mob.horse.leather', 'Horse Soft': 'mob.horse.soft', 'Horse Wood': 'mob.horse.wood', 'Donkey Angry': 'mob.horse.donkey.angry',
    'Donkey Death': 'mob.horse.donkey.death', 'Donkey Hit': 'mob.horse.donkey.hit', 'Donkey Idle': 'mob.horse.donkey.idle', 'Horse Skeleton Death': 'mob.horse.skeleton.death',
    'Horse Skeleton Hit': 'mob.horse.skeleton.hit', 'Horse Skeleton Idle': 'mob.horse.skeleton.idle', 'Horse Zombie Death': 'mob.horse.zombie.death', 'Horse Zombie Hit': 'mob.horse.zombie.hit',
    'Horse Zombie Idle': 'mob.horse.zombie.idle', 'Villager Death': 'mob.villager.death', 'Villager Haggle': 'mob.villager.haggle', 'Villager Hit': 'mob.villager.hit',
    'Villager Idle': 'mob.villager.idle', 'Villager No': 'mob.villager.no', 'Villager Yes': 'mob.villager.yes',
}


ALL_SOUNDS = ALL_SOUNDS_PRETTY | ALL_SOUNDS_RAW
