# Items

An `Item` describes a Minecraft item stack. Construct one directly or declare a
subclass (which also registers it as an importable — see
[Importables](./importables.md)).

```python
from pyhtsw import Item, Enchantment


sword = Item(
    key='diamond_sword',
    name='&bFrostbrand',
    lore='&7A chilling blade.\n&7Drops snow.',
    count=1,
    enchantments=[Enchantment('sharpness', 5)],
)
```

Common keyword arguments: `key` (required), `name`, `lore` (use `\n` for line
breaks), `count`, `enchantments`, `unbreakable`, `damage`, `color`,
`skull_data`, and the `hide_*_flag` toggles.

## Referencing items from actions

Actions like `give_item` accept an item in two forms; **you never pass a raw
string**:

```python
from pyhtsw import give_item, Item


# A declared subclass (the class) -> referenced by its htsw name
class Reward(Item, key='gold_ingot', name='&6Reward'):
    pass


give_item(Reward)

# An Item instance -> referenced by its written .snbt path
give_item(Item(key='apple'))

# Load an instance from an existing .snbt file
give_item(Item.from_path('items/some-item.snbt'))
```

- Pass an `Item` **subclass** to reference a declared item by name.
- Pass an `Item` **instance** to reference it by `.snbt` path (the file is
  written on export).
- Use `Item.from_path('....snbt')` to load an instance from a file rather than
  passing a string.

## SNBT

```python
print(Item(key='apple').into_snbt())          # indent=4 (default)
print(Item(key='apple').into_snbt(indent=None))  # compact
```

`Item.into_snbt(indent=4)` produces indented SNBT; pass `indent=None` for a
compact one-line form.

## Interaction keys

htsw assigns and manages item interaction keys automatically on import — you do
**not** manage them in PyHTSW.

See the [HTSW Importables reference](./htsw/importables.md) for the item section.
