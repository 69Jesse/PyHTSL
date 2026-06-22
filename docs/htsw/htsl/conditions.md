# Conditions

Conditions in HTSL are declared with a keyword and positional arguments. They
 are always within a Conditional Action's Conditions list (`if (...)`), and are
 separated by commas.

They may be typed on a single line or multiple lines:

```htsl
if (var x == 5, var y == 5) {}
// or
if (
    var x == 5,
    var y == 5
) {}
```

Every condition can be inverted by prefixing it with `!`.

## List of Conditions

<!--- TOC -->

- [Has Group](#has-group)
- [Compare Variable](#compare-variable)
- [Has Permission](#has-permission)
- [In Region](#in-region)
- [Has Item](#has-item)
- [Doing Parkour](#doing-parkour)
- [Has Potion Effect](#has-potion-effect)
- [Is Sneaking](#is-sneaking)
- [Is Flying](#is-flying)
- [Health](#health)
- [Max Health](#max-health)
- [Hunger](#hunger)
- [Gamemode](#gamemode)
- [Placeholder](#placeholder)
- [Has Team](#has-team)
- [Damage Cause](#damage-cause)
- [Can PvP](#can-pvp)
- [Fishing Environment](#fishing-environment)
- [Portal Type](#portal-type)
- [Block Type](#block-type)
- [Is Item](#is-item)
- [Damage Amount](#damage-amount)

<!--- END -->

### Has Group

```htsl
~if (
hasGroup "Group Name"
~) {}
```

To also match groups with a higher priority value:

```htsl
~if (
hasGroup "Group Name" true
~) {}
```

---

### Compare Variable

Use the `var` keyword for player variables:

```htsl
~if (
var x == 10
~) {}
```

`globalvar`:

```htsl
~if (
globalvar kills > 100
~) {}
```

`teamvar`:

```htsl
~if (
teamvar kills "Red Team" >= 50
~) {}
```

With Fallback Value:

```htsl
~if (
var score < 5 0
~) {}
```

Comparison is [typed with either a symbol or identifier](#comparison-operators).

---

### Has Permission

```htsl
~if (
hasPermission Fly
~) {}
```

Permission is typed with a (case insensitive) identifier:

| Permission              | Identifier              |
| ----------------------- | ----------------------- |
| Fly                     | Fly                     |
| Wood Door               | Wood_Door               |
| Iron Door               | Iron_Door               |
| Wood Trap Door          | Wood_Trap_Door          |
| Iron Trap Door          | Iron_Trap_Door          |
| Fence Gate              | Fence_Gate              |
| Button                  | Button                  |
| Lever                   | Lever                   |
| Use Launch Pads         | Use_Launch_Pads         |
| /tp                     | "/tp"                   |
| /tp Other Players       | "/tp Other Players"     |
| Jukebox                 | Jukebox                 |
| Kick                    | Kick                    |
| Ban                     | Ban                     |
| Mute                    | Mute                    |
| Pet Spawning            | Pet_Spawning            |
| Build                   | Build                   |
| Offline Build           | Offline_Build           |
| Fluid                   | Fluid                   |
| Pro Tools               | Pro_Tools               |
| Use Chests              | Use_Chests              |
| Use Ender Chests        | Use_Ender_Chests        |
| Item Editor             | Item_Editor             |
| Switch Game Mode        | Switch_Game_Mode        |
| Edit Stats              | Edit_Stats              |
| Change Player Group     | Change_Player_Group     |
| Change Gamerules        | Change_Gamerules        |
| Housing Menu            | Housing_Menu            |
| Team Chat Spy           | Team_Chat_Spy           |
| Edit Actions            | Edit_Actions            |
| Edit Regions            | Edit_Regions            |
| Edit Scoreboard         | Edit_Scoreboard         |
| Edit Event Actions      | Edit_Event_Actions      |
| Edit Commands           | Edit_Commands           |
| Edit Functions          | Edit_Functions          |
| Edit Inventory Layouts  | Edit_Inventory_Layouts  |
| Edit Teams              | Edit_Teams              |
| Edit Custom Menus       | Edit_Custom_Menus       |
| Item: Mailbox           | Item:_Mailbox           |
| Item: Egg Hunt          | Item:_Egg_Hunt          |
| Item: Teleport Pad      | Item:_Teleport_Pad      |
| Item: Launch Pad        | Item:_Launch_Pad        |
| Item: Action Pad        | Item:_Action_Pad        |
| Item: Hologram          | Item:_Hologram          |
| Item: NPCs              | Item:_NPCs              |
| Item: Action Button     | Item:_Action_Button     |
| Item: Leaderboard       | Item:_Leaderboard       |
| Item: Trash Can         | Item:_Trash_Can         |
| Item: Biome Stick       | Item:_Biome_Stick       |

---

### In Region

```htsl
~if (
inRegion "Spawn"
~) {}
```

---

### Has Item

```htsl
~if (
hasItem "Item Name"
~) {}
```

To specify What to Check, Where to Check, and the Required Amount:

```htsl
~if (
hasItem "Item Name" Item_Type Hand Equal_or_Greater_Amount
~) {}
```

What To Check is typed with a (case insensitive) identifier:

| What To Check | Identifier  |
| ------------- | ----------- |
| Item Type     | Item_Type   |
| Metadata      | Metadata    |

Where To Check:

| Where To Check | Identifier     |
| -------------- | -------------- |
| Hand           | Hand           |
| Armor          | Armor          |
| Hotbar         | Hotbar         |
| Inventory      | Inventory      |
| Cursor         | Cursor         |
| Crafting Grid  | Crafting_Grid  |
| Anywhere       | Anywhere       |

Required Amount:

| Required Amount           | Identifier                |
| ------------------------- | ------------------------- |
| Any Amount                | Any_Amount                |
| Equal or Greater Amount   | Equal_or_Greater_Amount   |

---

### Doing Parkour

```htsl
~if (
doingParkour
~) {}
```

---

### Has Potion Effect

```htsl
~if (
hasPotion Speed
~) {}
```

Effect is typed with a (case insensitive) identifier:

| Effect            | Identifier        |
| ----------------- | ----------------- |
| Speed             | Speed             |
| Slowness          | Slowness          |
| Haste             | Haste             |
| Mining Fatigue    | Mining_Fatigue    |
| Strength          | Strength          |
| Instant Health    | Instant_Health    |
| Instant Damage    | Instant_Damage    |
| Jump Boost        | Jump_Boost        |
| Nausea            | Nausea            |
| Regeneration      | Regeneration      |
| Resistance        | Resistance        |
| Fire Resistance   | Fire_Resistance   |
| Water Breathing   | Water_Breathing   |
| Invisibility      | Invisibility      |
| Blindness         | Blindness         |
| Night Vision      | Night_Vision      |
| Hunger            | Hunger            |
| Weakness          | Weakness          |
| Poison            | Poison            |
| Wither            | Wither            |
| Health Boost      | Health_Boost      |
| Absorption        | Absorption        |

---

### Is Sneaking

```htsl
~if (
isSneaking
~) {}
```

---

### Is Flying

```htsl
~if (
isFlying
~) {}
```

---

### Health

```htsl
~if (
health < 10
~) {}
```

Comparison is [typed with either a symbol or identifier](#comparison-operators).

---

### Max Health

```htsl
~if (
maxHealth == 20
~) {}
```

Comparison is [typed with either a symbol or identifier](#comparison-operators).

---

### Hunger

```htsl
~if (
hunger > 10
~) {}
```

Comparison is [typed with either a symbol or identifier](#comparison-operators).

---

### Gamemode

```htsl
~if (
gamemode Creative
~) {}
```

Gamemode is typed with a (case insensitive) identifier:

| Gamemode  | Identifier |
| --------- | ---------- |
| Adventure | Adventure  |
| Survival  | Survival   |
| Creative  | Creative   |

---

### Placeholder

```htsl
~if (
placeholder %player.health% >= 20
~) {}
```

A fallback value can be provided for when the placeholder resolves to nothing:

```htsl
~if (
placeholder %var.player/kills% > 100 0
~) {}
```

Comparison is [typed with either a symbol or identifier](#comparison-operators).

---

### Has Team

```htsl
~if (
hasTeam "Red Team"
~) {}
```

---

### Damage Cause

```htsl
~if (
damageCause Fall
~) {}
```

Cause is typed with a (case insensitive) identifier:

| Cause          | Identifier     |
| -------------- | -------------- |
| Entity Attack  | Entity_Attack  |
| Projectile     | Projectile     |
| Suffocation    | Suffocation    |
| Fall           | Fall           |
| Lava           | Lava           |
| Fire           | Fire           |
| Fire Tick      | Fire_Tick      |
| Drowning       | Drowning       |
| Starvation     | Starvation     |
| Poison         | Poison         |
| Thorns         | Thorns         |

---

### Can PvP

```htsl
~if (
canPvp
~) {}
```

---

### Fishing Environment

```htsl
~if (
fishingEnv Lava
~) {}
```

Environment is typed with a (case insensitive) identifier:

| Environment | Identifier |
| ----------- | ---------- |
| Water       | Water      |
| Lava        | Lava       |

---

### Portal Type

```htsl
~if (
portal Nether_Portal
~) {}
```

Portal Type is typed with a (case insensitive) identifier:

| Portal Type   | Identifier     |
| ------------- | -------------- |
| Nether Portal | Nether_Portal  |
| End Portal    | End_Portal     |

---

### Block Type

```htsl
~if (
blockType Stone
~) {}
```

---

### Is Item

```htsl
~if (
isItem Diamond_Sword
~) {}
```

---

### Damage Amount

```htsl
~if (
damageAmount > 5
~) {}
```

Comparison is [typed with either a symbol or identifier](#comparison-operators).

---

## References

### Comparison Operators

Comparisons can be typed with either a symbol or identifier:

| Comparison            | Symbol | Identifier             |
| --------------------- | ------ | ---------------------- |
| Equal                 | ==     | Equal                  |
| Less Than             | <      | Less Than              |
| Less Than or Equal    | <=     | Less Than or Equal     |
| Greater Than          | >      | Greater Than           |
| Greater Than or Equal | >=     | Greater Than or Equal  |

---

### Inversion

Every condition can be inverted by prefixing it with `!`:

```htsl
~if (
!isSneaking
~) {}
```

```htsl
~if (
!gamemode Creative
~) {}
```

---

### Condition Notes

A condition can be annotated with a note by placing a `///` line above it inside
 the `if` block:

```htsl
if (
    /// must be a resident or higher
    hasGroup "Resident" true,
    /// no creative CHEATERS!!!
    !gamemode Creative
) {}
```

---