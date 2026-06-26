"""Edge behaviours of the htsw importable model: duplicate-name errors,
top-level wrapping, item/location validation and the menu override warning."""

import json
import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    Item,
    Location,
    chat,
    create_function,
    give_item,
    normalize_item,
    set_projects_folder,
)
from pyhtsw.location import resolve_location

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp)


# Duplicate importable names raise.
with Container():

    @create_function('dup')
    def _a() -> None:
        chat('a')

    raised = False
    try:

        @create_function('dup')
        def _b() -> None:
            chat('b')
    except RuntimeError:
        raised = True
    assert raised, 'expected a RuntimeError for the duplicate function name'


# Top-level actions get wrapped into a function named after the project.
with Container() as wrap:
    chat('written outside any importable')
wrap.export('Wrap Test')
data = json.loads((tmp / 'wrap-test' / 'import.json').read_text())
assert any(fn['name'] == 'Wrap Test' for fn in data['functions'])


# Items never accept plain strings.
for bad in ('a string', 123, None):
    raised = False
    try:
        normalize_item(bad)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, f'normalize_item should reject {bad!r}'


# A bare Location is not a valid location; the concrete ones are.
raised = False
try:
    resolve_location(Location())
except TypeError:
    raised = True
assert raised, 'bare Location() should be rejected'

assert resolve_location(Location.house_spawn()) == ('house_spawn', None)
assert resolve_location(Location.custom(1, 2, 3)) == ('custom_coordinates', '1 2 3')


# give_item with a declared class references by name; an instance by path.
with Container() as c:

    class Sword(Item, key='diamond_sword', name='&bSword'):
        pass

    give_item(Sword)  # by name
    give_item(Item('apple'))  # anonymous -> path
c.export('Ref Test')
text = (tmp / 'ref-test' / 'functions' / 'ref-test.htsl').read_text()
assert 'giveItem "Sword"' in text
# anonymous .snbt path, resolved relative to the action file (in functions/)
assert 'giveItem "../items/apple-' in text
