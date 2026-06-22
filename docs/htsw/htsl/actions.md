# Actions

Actions in HTSL are declared with a keyword and positional arguments.

```htsl
chat "Hello, World!"
tp Custom_Coordinates "0 0 0"
```

A newline terminates an action; All positional arguments must be on the same
 line.

## List of Actions

<!--- TOC -->

- [Conditional](#conditional)
- [Change Player's Group](#change-players-group)
- [Kill Player](#kill-player)
- [Full Heal](#full-heal)
- [Display Title](#display-title)
- [Display Action Bar](#display-action-bar)
- [Reset Inventory](#reset-inventory)
- [Change Max Health](#change-max-health)
- [Parkour Checkpoint](#parkour-checkpoint)
- [Give Item](#give-item)
- [Remove Item](#remove-item)
- [Send a Chat Message](#send-a-chat-message)
- [Apply Potion Effect](#apply-potion-effect)
- [Clear All Potion Effects](#clear-all-potion-effects)
- [Give Experience Levels](#give-experience-levels)
- [Send to Lobby](#send-to-lobby)
- [Change Variable](#change-variable)
- [Teleport Player](#teleport-player)
- [Fail Parkour](#fail-parkour)
- [Play Sound](#play-sound)
- [Set Compass Target](#set-compass-target)
- [Set Gamemode](#set-gamemode)
- [Change Health](#change-health)
- [Change Hunger Level](#change-hunger-level)
- [Random Action](#random-action)
- [Trigger Function](#trigger-function)
- [Apply Inventory Layout](#apply-inventory-layout)
- [Enchant Held Item](#enchant-held-item)
- [Pause Execution](#pause-execution)
- [Set Player Team](#set-player-team)
- [Display Menu](#display-menu)
- [Drop Item](#drop-item)
- [Change Velocity](#change-velocity)
- [Launch to Target](#launch-to-target)
- [Set Player Weather](#set-player-weather)
- [Set Player Time](#set-player-time)
- [Toggle Nametag Display](#toggle-nametag-display)

<!--- END -->

### Conditional

```htsl
~var x = 10
~var y = 10
if (var x > 5, var y > 5) {
    chat "x and y are greater than 5"
}
```

Match Any Condition is implicitly false. to set it explicitly, use `or` (true) 
 or `and` (false) before the Condition list:

```htsl
~var x = 0
~var y = 10
if or (var x > 5, var y > 5) {
    chat "x is greater than 5 or y is greater than 5"
}
```

To declare Else Actions, use the optional `else` keyword:

```htsl
~var x = 0
~var y = 10
~var z = 0
if (
    var x == 0,
    var y == 0,
    var z == 0,
) {
    chat "Position is at the origin"
} else {
    chat "Position is not at the origin"
}
```

---

### Change Player's group

```htsl
changePlayerGroup "Winner"
```

---

To enable Demotion Protection:

```htsl
changePlayerGroup "Winner" true
```

---

### Kill Player

```htsl
kill
```

---

### Full Heal

```htsl
fullHeal
```

---

### Display Title

```htsl
title "Hello"
```

To set Subtitle:

```htsl
title "Hello" "World"
```

To set Fadein, Stay, and Fadeout:

```htsl
title "Hello" "World" 1 2 1
```

---

### Display Action Bar

```htsl
actionBar "Hello, World!"
```

---

### Reset Inventory

```htsl
resetInventory
```

---

### Change Max Health

```htsl
maxHealth = 5
```

Change Max Health operations can be
 [typed with either a symbol or identifier](#operations).

---

### Parkour Checkpoint

```htsl
parkCheck
```

---

### Give Item

```htsl
// giveItem [Item] [Allow Multiple] [Inventory Slot] [Replace Existing Item]
giveItem "Item Name" true First_Available_Slot false
```

> Item is set by referencing the name of an existing item declared in
`import.json`.

Inventory Slot can be typed with a (case insensitive) identifier or an index:

| Inventory Slot       | Identifier           | Index |
| -------------------- | -------------------- | ----- |
| First Available Slot | First_Available_Slot | -1    |
| Hand Slot            | Hand_Slot            | -2    |
| Hotbar Slot          |                      | 0..8  |
| Inventory Slot       |                      | 9..35 |
| Boots                | Boots                | 36    |
| Leggings             | Leggings             | 37    |
| Chestplate           | Chestplate           | 38    |
| Helmet               | Helmet               | 39    |

---

### Remove Item

```htsl
removeItem "Item Name"
```

---

> Item is set by referencing the name of an existing item declared in
`import.json`.

### Send a Chat Message

```htsl
chat "Hello, World!"
```

---

### Apply Potion Effect


---

### Clear All Potion Effects

```htsl
clearEffects
```

---

### Give Experience Levels

```htsl
xpLevel 10
```

---

### Send to Lobby


---

### Change Variable

Declare a Change Variable action starting with a keyword, `var`,
 `globalvar`, or `teamvar`, followed by the name of the variable.

Use the `var` keyword to declare a Change Variable action with the player
 holder.

```htsl
var x = 5
```

Change Variable Actions with the global and team holders can be declared
 similarly:

```htsl
// global variable x
globalvar x = 5

// team variable x for team Red
teamvar x Red = 5
```

Operation can be typed with either a symbol or identifier:

| Operation              | Symbol | Identifier             |
| ---------------------- | ------ | ---------------------- |
| Set                    | =      | Set                    |
| Unset                  |        | Unset                  |
| Increment              | +=     | Increment              |
| Decrement              | -=     | Decrement              |
| Multiply               | *=     | Multiply               |
| Divide                 | /=     | Divide                 |
| Bitwise AND            | &=     | Bitwise_AND            |
| Bitwise OR             | \|=    | Bitwise_OR             |
| Bitwise XOR            | ^=     | Bitwise_XOR            |
| Left Shift             | <<=    | Left_Shift             |
| Arithmetic Right Shift | >>=    | Arithmetic_Right_Shift |
| Logical Right Shift    | >>>=   | Logical_Right_Shift    |

---

### Teleport Player

```htsl
tp Custom_Coordinates "0 0 0"
```

To enable Prevent Teleport Inside Blocks:

```htsl
tp Custom_Coordinates "0 0 0" true
```

Location is [typed with an identifier](#locations).

---

### Fail Parkour

```htsl
failParkour "Reason"
```

---

### Play Sound



---

### Set Compass Target

---

```htsl
compassTarget House_Spawn_Location
```

Location is [typed with an identifier](#locations).

---

### Set Gamemode

```htsl
gamemode Creative
```

Gamemode is typed with a (case insensitive) identifier:

| Gamemode  | Identifier |
| --------- | ---------- |
| Adventure | Adventure  |
| Survival  | Survival   |
| Creative  | Creative   |

---

### Change Health

```htsl
changeHealth = 5
```

---

Change Health operations can be
 [typed with either a symbol or identifier](#operations).

---

### Change Hunger Level

```htsl
hungerLevel = 5
```

Change Hunger Level operations can be
 [typed with either a symbol or identifier](#operations).

---

### Random Action

```htsl
random {
    var reward = 5
    var reward = 10
    var reward = 20
}
~chat "Reward: %var.player/reward%"
```

---

### Trigger Function

```htsl
function "My Function"
```

To set Trigger For All Players:

```htsl
// Runs for all players in the Housing
function "My Function" true
```

---

### Apply Inventory Layout

```htsl
applyLayout "PvP Layout"
```

---

### Enchant Held Item


---

### Pause Execution

```htsl
pause 5
```

---

### Set Player Team

```htsl
setTeam "Red Team"
```

---

### Display Menu

```htsl
displayMenu "My Menu"
```

---

### Drop Item

```htsl
dropItem "Item Name" Invokers_Location true true true true
```

---

Location is [typed with an identifier](#locations).

### Change Velocity

```htsl
changeVelocity 0 10 0
```

---

### Launch to Target

```htsl
launchTarget Custom_Coordinates "~ ~10 ~" 3
```

---

Location is [typed with an identifier](#locations).

### Set Player Weather


---

### Set Player Time

```htsl
playerTime 1000
```

---

### Toggle Nametag Display

```htsl
displayNametag false
```

---

## References

### Operations

Operations can be typed with either a symbol or identifier:

| Operation | Symbol | Identifier |
| ----------| ------ | ---------- |
| Set       | =      | Set        |
| Increment | +=     | Increment  |
| Decrement | -=     | Decrement  |
| Multiply  | *=     | Multiply   |
| Divide    | /=     | Divide     |

---

### Locations

Locations are typed with a (case insensitive) identifier:

| Location             | Identifier           |
| -------------------- | -------------------- |
| House Spawn Location | House_Spawn_Location |
| Invokers Location    | Invokers_Location    |
| Current Location     | Current_Location     |
| Custom Coordinates   | Custom_Coordinates   |

Custom Coordinates must be followed by a coordinate string.

---

### Action Notes

An action can be annotated with a note by placing a `///` line above it.

```htsl
/// Clear the player's coins if they have more than 10
if (var coins > 10) {
    var coins = 0
}

/// You can see this note in-game!
chat "Hello, World"
```

Note that you will get an error for orphaned notes:

```htsl
var x = 5

/// Orphaned comment
```

---
