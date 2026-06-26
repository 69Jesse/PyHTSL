"""Multi-folder htsw export: one folder per Python module mirroring the package
tree, package-tree `include`s, cross-module include edges, cycle-skip, and
per-module .snbt placement. Modules are assigned by hand here so the tree shape
is explicit; real `__module__` capture is exercised by the example projects."""

import json
import tempfile
from pathlib import Path
from types import ModuleType

import pyhtsw
from pyhtsw import (
    Container,
    Item,
    chat,
    create_function,
    give_item,
    set_projects_folder,
    trigger_function,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp)

with Container() as container:

    @create_function('Ability')
    def ability() -> None:
        chat('cast')

    @create_function('Combat')
    def combat() -> None:
        chat('hit')

    # An anonymous item owned by items.abilities but handed out from a function
    # in features.cookie -> its .snbt must live under the abilities folder.
    potion = Item('potato', name='&aPotion')

    @create_function('Cookie')
    def cookie() -> None:
        chat('tick')
        trigger_function(
            ability
        )  # cross-module edge: features.cookie -> items.abilities
        give_item(potion)

    # Mutually-recursive functions in two modules -> an include cycle that must
    # be broken (exactly one direction kept).
    @create_function('PingA')
    def ping_a() -> None:
        trigger_function('PingB')

    @create_function('PingB')
    def ping_b() -> None:
        trigger_function('PingA')


potion.__htsw_module__ = 'items.abilities'
ability.__htsw_importable__.module = 'items.abilities'
combat.__htsw_importable__.module = 'features.general.combat'
cookie.__htsw_importable__.module = 'features.cookie'
ping_a.__htsw_importable__.module = 'modx'
ping_b.__htsw_importable__.module = 'mody'

container.export('Tree Demo')
root = tmp / 'tree-demo'


def load(relpath: str) -> dict:
    return json.loads((root / relpath).read_text(encoding='utf-8'))


def includes(relpath: str) -> set[str]:
    return set(load(relpath).get('include', []))


# Root mirrors the top-level packages/modules (kebab-case), not the functions.
assert 'functions' not in load('import.json')
assert includes('import.json') == {
    'modules/features/import.json',
    'modules/items/import.json',
    'modules/modx/import.json',
    'modules/mody/import.json',
}

# Packages include their children; the leaf holds the actual function.
assert includes('modules/features/import.json') == {
    'modules/cookie/import.json',
    'modules/general/import.json',
}
assert includes('modules/features/modules/general/import.json') == {
    'modules/combat/import.json',
}
combat_node = load('modules/features/modules/general/modules/combat/import.json')
assert {fn['name'] for fn in combat_node['functions']} == {'Combat'}

# Cross-module reference -> include edge into the other subtree, with a relative
# path that resolves to the abilities import.json.
cookie_dir = root / 'modules/features/modules/cookie'
cookie_includes = includes('modules/features/modules/cookie/import.json')
assert len(cookie_includes) == 1
(edge,) = cookie_includes
assert (cookie_dir / edge).resolve() == (
    root / 'modules/items/modules/abilities/import.json'
).resolve()

# The cycle is broken: exactly one of the two directions survives.
modx_to_mody = 'mody' in str(includes('modules/modx/import.json'))
mody_to_modx = 'modx' in str(includes('modules/mody/import.json'))
assert modx_to_mody != mody_to_modx, (modx_to_mody, mody_to_modx)

# The anonymous potion .snbt lands under its owning module (items.abilities),
# and the give-item action in features.cookie references it by a path that
# resolves to that file.
snbts = list((root / 'modules/items/modules/abilities/items').glob('*.snbt'))
assert snbts, 'potion .snbt was not placed under the owning module'
give = (cookie_dir / 'functions/cookie.htsl').read_text(encoding='utf-8')
ref = next(line.split('"')[1] for line in give.splitlines() if '.snbt' in line)
assert (cookie_dir / 'functions' / ref).resolve() == snbts[0].resolve()

# Exporting a single module roots it at the project root, with anything it pulls
# in from another package nesting as a referenced sub-project.
with Container():

    @create_function('Leaf')
    def leaf() -> None:
        trigger_function('Dep')

    @create_function('Dep')
    def dep() -> None:
        chat('dep')


leaf.__htsw_importable__.module = 'pkg.leaf'
dep.__htsw_importable__.module = 'other.dep'

module = ModuleType('pkg.leaf')
module.leaf = leaf  # type: ignore[attr-defined]
module.dep = dep  # type: ignore[attr-defined]
pyhtsw.export(module, 'Mod Root')

mod_root = tmp / 'mod-root'
mod_data = json.loads((mod_root / 'import.json').read_text(encoding='utf-8'))
# the exported module's own function is at the root...
assert {fn['name'] for fn in mod_data['functions']} == {'Leaf'}
# ...and its out-of-package dependency nests under its real path.
assert 'modules/other/import.json' in mod_data.get('include', [])
dep_data = json.loads(
    (mod_root / 'modules/other/modules/dep/import.json').read_text(encoding='utf-8'),
)
assert {fn['name'] for fn in dep_data['functions']} == {'Dep'}

print('test_htsw_module_tree passed')
