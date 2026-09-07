from typing import cast

from pyhtsw import (
    NPC,
    Container,
    Enchantment,
    GlobalStat,
    IfAll,
    Item,
    Location,
    NoTypeCasting,
    PlayerStat,
    TeamStat,
    apply_potion_effect,
    chat,
    display_action_bar,
    display_title,
    enchant_held_item,
    fail_parkour,
    launch_to_target,
    pause_execution,
)
from pyhtsw.declarations.item_keys import ItemKey
from pyhtsw.execute.java_string import java_string_length
from pyhtsw.stats.stat import Stat, StatNameError


def rejects(exc: type[Exception], label: str, call) -> None:
    try:
        call()
    except exc:
        return
    raise AssertionError(f'{label} should have been rejected')


assert java_string_length('abc') == 3
assert java_string_length('a\U0001f600b') == 4


for name in ('seventeen_chars_x', 'with space', ''):
    rejects(StatNameError, f'PlayerStat({name!r})', lambda n=name: PlayerStat(n))
    rejects(StatNameError, f'GlobalStat({name!r})', lambda n=name: GlobalStat(n))

rejects(
    StatNameError,
    'TeamStat team name',
    lambda: TeamStat('k', team='a_team_name_too_long'),
)

assert PlayerStat('sixteen_chars_xx').name == 'sixteen_chars_xx'

# A placeholder body is not a var-name position, so scanning text for stat
# references must tolerate one htsw would never have parsed as a name.
from pyhtsw.checkable import Checkable  # noqa: E402

refs = list(
    Checkable.iter_in_string('%var.player/way_too_long_a_name% %var.player/ok%'),
)
assert all(isinstance(ref, Stat) for ref in refs), refs
assert [cast('Stat', ref).name for ref in refs] == ['ok'], refs


def assign_over_limit() -> None:
    with Container():
        PlayerStat('t').as_double().value = GlobalStat('fifteen_chars_x').as_double()


rejects(ValueError, 'over-long rhs placeholder', assign_over_limit)


def compare_over_limit() -> None:
    with Container():
        with IfAll(
            PlayerStat('t').as_double() < GlobalStat('fifteen_chars_x').as_double(),
        ):
            chat('hi')


rejects(ValueError, 'over-long compared value', compare_over_limit)


# One character shorter fits, so the limit is exact rather than approximate.
with Container() as container:
    PlayerStat('t').as_double().value = GlobalStat('fourteen_chars').as_double()

assert container.into_htsl() == ('var "t" = "%var.global/fourteen_chars 0.0%D" true'), (
    container.into_htsl()
)


# The cap is on a *quoted* value only. A bare placeholder is accepted at any
# length, so dropping the type suffix that forces the quotes lifts it.
with NoTypeCasting():
    with Container() as container:
        PlayerStat('t').as_double().value = GlobalStat('sixteen_chars_xx').as_double()
        with IfAll(
            PlayerStat('t').as_double() < GlobalStat('sixteen_chars_xx').as_double(),
        ):
            chat('hi')
    htsl = container.into_htsl()

assert htsl == (
    'var "t" = %var.global/sixteen_chars_xx 0.0% true\n'
    'if and (var "t" < %var.global/sixteen_chars_xx 0.0% 0.0) {\n'
    '    chat "hi"\n'
    '}'
), htsl


# A quoted value is measured the way htsw's parser reads it back, so an escaped
# quote counts as the one character it is typed as.
with Container() as container:
    PlayerStat('s').as_string().value = '"' * 32

assert container.into_htsl() == 'var "s" = "{}" true'.format('\\"' * 32), (
    container.into_htsl()
)


def escaped_quotes_over_limit() -> None:
    with Container():
        PlayerStat('s').as_string().value = '"' * 33


rejects(ValueError, 'over-long escaped string value', escaped_quotes_over_limit)


def over_chat_limit(call) -> None:
    with Container():
        call()


for label, call in (
    ('chat', lambda: chat('x' * 257)),
    ('display_title', lambda: display_title('x' * 257)),
    ('display_action_bar', lambda: display_action_bar('x' * 257)),
    ('fail_parkour', lambda: fail_parkour('x' * 257)),
):
    rejects(ValueError, label, lambda c=call: over_chat_limit(c))


# htsw rejects an empty MESSAGE, TITLE title and ACTION_BAR text; `&r` is the
# shortest thing Housing accepts in their place.
with Container() as container:
    chat('')
    display_title('')
    display_action_bar('')

assert container.into_htsl() == ('chat "&r"\ntitle "&r" "&r" 1 5 1\nactionBar "&r"'), (
    container.into_htsl()
)


for label, call in (
    ('pause_execution', lambda: pause_execution(1001)),
    ('display_title fadein', lambda: display_title('a', 'b', fadein=6)),
    ('display_title stay', lambda: display_title('a', 'b', stay=11)),
    ('apply_potion_effect duration', lambda: apply_potion_effect('speed', duration=0)),
    ('apply_potion_effect level', lambda: apply_potion_effect('speed', level=11)),
    (
        'enchant_held_item level',
        lambda: enchant_held_item(Enchantment('sharpness', 11)),
    ),
    (
        'launch_to_target strength',
        lambda: launch_to_target(Location.custom(1, 2, 3), strength=21),
    ),
):
    rejects(ValueError, label, lambda c=call: over_chat_limit(c))


for key in (
    'monster_spawner',
    'farmland',
    'command_block',
    'minecart_with_command_block',
    'brown_mushroom_block',
    'red_mushroom_block',
):
    rejects(ValueError, f'Item({key!r})', lambda k=key: Item(cast('ItemKey', k)))

rejects(ValueError, 'Item count 65', lambda: Item('stone', count=65))
assert Item('stone', count=64).count == 64


def duplicate_npc_position() -> None:
    with Container():
        NPC('A', (1, 2, 3))
        NPC('B', (1, 2, 3))


rejects(RuntimeError, 'duplicate NPC position', duplicate_npc_position)
