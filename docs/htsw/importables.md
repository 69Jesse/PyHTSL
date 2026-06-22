# Importables

Importables are the basis of HTSW. An *importable* is an entity that can be
 imported into a housing. Think functions, items, regions, etc.

Instead of importing HTSL files directly, you instead declare housing objects
 that you want to import in an `import.json` file:
 
```json
{
  "functions": [ /* ... */ ],
  "events":    [ /* ... */ ],
  "items":     [ /* ... */ ],
  "regions":   [ /* ... */ ],
  "menus":     [ /* ... */ ]
}
```

## Example Importable

An example importable for a player welcoming feature might look something like
 this:

```json
{
  "functions": [
    { "name": "Global Welcome", "actions": "src/global_welcome.htsl" },
    { "name": "Global Welcome Back", "actions": "src/global_welcome_back.htsl" },
  ],
  "events": [
    { "event": "Player Join", "actions": "src/events/player_join.htsl" }
  ]
}
```

## List of Importables

<!--- TOC -->

- [Function](#function)
- [Event](#event)
- [Item](#item)
- [Region](#region)
- [Menu](#menu)

<!--- END -->

### Function

Required fields: `name`, `actions`.

```json
{
  "functions": [
    { "name": "My Function!", "actions": "src/my_function.htsl" },
    { "name": "My Second Function!", "actions": "src/my_second_function.htsl" }
  ]
}
```

Where `name` is the name of the function in-game, and `actions` is a path to a
 `.htsl` file containing your actions.

Functions can also declare `repeatTicks`, `description`, and an `icon`:

```json
{
  "functions": [
    {
      "name": "Loop 10t",
      "actions": "src/loop_10t.htsl",
      "repeatTicks": 10,
      "icon": {
        "item": "minecraft:clock",
        "count": 10
      }
    }
  ]
}
```

Existing functions are **matched by name** during import — renaming a function
 will create a new one and leave the old one orphaned.

---

### Event

Required fields: `event`, `actions`.

```json
{
  "events": [
    {
      "event": "Player Join",
      "actions": "src/on_join.htsl"
    }
  ]
}
```

`event` must be one of Housing's built-in event names.

---

### Item

Required fields: `name`, `nbt`.

```json
{
  "items": [
    {
      "name": "Magic Wand",
      "nbt": "items/magic_wand.snbt",
      "rightClickActions": "src/use_magic_wand.htsl"
    }
  ]
}
```

`name` is a stable identifier used from HTSL (`giveItem "Magic Wand"`). It
 is not the item's actual display name, which is separately declared in the nbt
 file.

`nbt` is a path to a **S**tringified **NBT** file (also known as Mojangson),
 containing the item's NBT data. See
 [here](https://minecraft.wiki/w/NBT_format#SNBT_format) for more information.

---

### Region

Required fields: `name`, `bounds`.

```json
{
  "regions": [
    {
      "name": "Spawn",
      "bounds": {
        "from": { "x": 0, "y": 100, "z": 0 },
        "to":   { "x": 10, "y": 110, "z": 10 }
      },
      "onEnterActions": "src/enter_spawn.htsl",
      "onExitActions": "src/exit_spawn.htsl"
    }
  ]
}
```

`bounds` is defined by two corners, `from` and `to`. `onEnterActions` and
 `onExitActions` are optional `.htsl` files that fire when a player enters or
 leaves the region.

---

### Menu

Required fields: `name`, `size`, `slots`.

```json
{
  "menus": [
    {
      "name": "Shop",
      "size": 3,
      "slots": [
        {
          "slot": 13,
          "nbt": "src/shop/emerald.snbt",
          "actions": "src/shop/buy_emerald.htsl"
        }
      ]
    }
  ]
}
```

`size` is the number of rows (1–6, 9 slots each). Each entry in `slots` has a
 `slot` index (0–53), an `nbt` file for the displayed item, and an optional
 `actions` file for click handling.

Open the menu from HTSL with `displayMenu "Shop"`.

---

## "Include" and Project Structure

`import.json` takes a field `include` which specifies other `import.json` files
 to include the contents of in this one.

```json
{
  "include": [
    "other_1/import.json",
    "other_2/import.json"
  ]
}
```

This allows you to split content into more self-contained `import.json` modules
 instead of putting all of your code for a house in one place, while keeping it
 in one importable package.

An opinionated project structure for an entire house might look something like
 this:

```
house
├── import.json
├── core
│   ├── src
│   └── import.json
├── crates
│   ├── src
│   └── import.json
└── parkour
    ├── src
    └── import.json
```

With the root `import.json` being simply:

```json
{
  "include": [
    "core/import.json",
    "crates/import.json",
    "parkour/import.json"
  ]
}
```

> Note that no structure or conventions are enforced by HTSW. You may lay your
 project out however you like.