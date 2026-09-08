import re
import warnings

from pyhtsw import (
    Container,
    EmulatedHouse,
    GlobalStat,
    IfAll,
    PlayerStat,
    PyHTSWWarning,
    TemporaryStat,
    function,
)
from pyhtsw.ext import (
    distance_squared,
    gather_from_all_players,
    nearest_position,
    select_max,
    select_min,
)

# === select_min keeps the smallest key and copies that row's payload ===

with EmulatedHouse(ignore_action_limits=True) as house:
    rows = [
        (GlobalStat(f'sk{i}').as_long(), GlobalStat(f'sn{i}').as_string())
        for i in range(4)
    ]
    for (key_stat, name_stat), (key, name) in zip(
        rows,
        ((50, 'e'), (20, 'b'), (70, 'g'), (30, 'c')),
        strict=True,
    ):
        house.put(key_stat, key, ignore_warning=True)
        house.put(name_stat, name, ignore_warning=True)

    winner = GlobalStat('swin').as_string().with_auto_unset(False)
    best = select_min(
        rows,
        key=lambda row: row[0],
        payload=lambda row: row[1],
        output=winner,
    )

    def check_min() -> None:
        assert str(house.get_raw(winner)) == 'b', house.get_raw(winner)
        assert int(house.get_raw(best)) == 20, house.get_raw(best)

    house.assert_all(check_min)


# === select_max, and `where` excludes a candidate ===

with EmulatedHouse(ignore_action_limits=True) as house:
    rows = [
        (GlobalStat(f'mk{i}').as_long(), GlobalStat(f'mn{i}').as_string())
        for i in range(3)
    ]
    for (key_stat, name_stat), (key, name) in zip(
        rows,
        ((10, 'a'), (99, 'skipped'), (40, 'd')),
        strict=True,
    ):
        house.put(key_stat, key, ignore_warning=True)
        house.put(name_stat, name, ignore_warning=True)

    winner = GlobalStat('mwin').as_string().with_auto_unset(False)
    select_max(
        rows,
        key=lambda row: row[0],
        payload=lambda row: row[1],
        output=winner,
        where=lambda row: row[0] < 90,
    )

    def check_max() -> None:
        assert str(house.get_raw(winner)) == 'd', house.get_raw(winner)

    house.assert_all(check_max)


# === nearest_position picks the closest, and honours `within` ===

with EmulatedHouse(ignore_action_limits=True) as house:
    points = [
        (
            GlobalStat(f'px{i}').as_double(),
            GlobalStat(f'py{i}').as_double(),
            GlobalStat(f'pz{i}').as_double(),
        )
        for i in range(3)
    ]
    for point, (x, y, z) in zip(
        points,
        ((100.0, 0.0, 0.0), (3.0, 4.0, 0.0), (50.0, 0.0, 0.0)),
        strict=True,
    ):
        for stat, value in zip(point, (x, y, z), strict=True):
            house.put(stat, value, ignore_warning=True)

    out = tuple(
        PlayerStat(f'no{axis}').as_double().with_auto_unset(False) for axis in 'xyz'
    )
    nearest_position(
        points,
        output=out,
        to=(0.0, 0.0, 0.0),
        within=10.0,
        if_none=(-1.0, -1.0, -1.0),
    )

    def check_nearest() -> None:
        assert float(house.get_raw(out[0])) == 3.0, house.get_raw(out[0])
        assert float(house.get_raw(out[1])) == 4.0, house.get_raw(out[1])

    house.assert_all(check_nearest)


with EmulatedHouse(ignore_action_limits=True) as house:
    far = [
        (
            GlobalStat('fx').as_double(),
            GlobalStat('fy').as_double(),
            GlobalStat('fz').as_double(),
        ),
    ]
    for stat, value in zip(far[0], (900.0, 0.0, 0.0), strict=True):
        house.put(stat, value, ignore_warning=True)

    out = tuple(
        PlayerStat(f'fo{axis}').as_double().with_auto_unset(False) for axis in 'xyz'
    )
    nearest_position(
        far,
        output=out,
        to=(0.0, 0.0, 0.0),
        within=10.0,
        if_none=(-1.0, -1.0, -1.0),
    )

    def check_none() -> None:
        assert float(house.get_raw(out[0])) == -1.0, house.get_raw(out[0])

    house.assert_all(check_none)


# === The key is computed once per candidate, not once per use ===

with Container() as container:
    points = [
        (
            GlobalStat(f'qx{i}').as_double(),
            GlobalStat(f'qy{i}').as_double(),
            GlobalStat(f'qz{i}').as_double(),
        )
        for i in range(3)
    ]
    out = tuple(
        PlayerStat(f'qo{axis}').as_double().with_auto_unset(False) for axis in 'xyz'
    )

    @function('Nearest')
    def nearest() -> None:
        nearest_position(points, output=out, within=16.0)


htsl = container.into_htsl()
# Three axes, each read once per candidate. A second flatten would double it.
assert htsl.count('%var.global/qx0 0.0%D') == 2, htsl  # distance, then payload
assert htsl.count('%var.global/qy0 0.0%D') == 2, htsl
# Scratch does not grow with the candidate count.
assert len({int(n) for n in re.findall(r'tmp(\d+)', htsl)}) <= 8, htsl


# === distance_squared reuses the scratch it is handed ===

with Container() as container:

    @function('Distance')
    def distance() -> None:
        total = TemporaryStat().as_double()
        axis = TemporaryStat().as_double()
        for i in range(3):
            distance_squared(
                (GlobalStat(f'dx{i}').as_double(), GlobalStat(f'dy{i}').as_double()),
                (0.0, 0.0),
                into=total,
                axis=axis,
            )


assert len({int(n) for n in re.findall(r'tmp(\d+)', container.into_htsl())}) == 2


# === gather_from_all_players emits the reset, the trigger and the guard ===

with Container() as container:
    tally = GlobalStat('afkn').as_long()
    total = GlobalStat('afktot').as_long()

    @gather_from_all_players('Count', require_all=True)
    def count() -> None:
        tally.value += 1

    @function('Use')
    def use() -> None:
        with count.gather(reset=tally):
            total.value += tally


htsl = container.into_htsl()
assert 'globalvar "gathered" += 1' in htsl, htsl
assert 'globalvar "afkn" = 0' in htsl, htsl
assert 'function "Count" true' in htsl, htsl
assert '!globalvar "gathered" == "%house.players%L"' in htsl, htsl


# === Re-using one expression across two statements warns ===

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    with Container():
        a = PlayerStat('wa').as_long()

        @function('Reused')
        def reused() -> None:
            best = TemporaryStat().as_long().with_value(0)
            computed = (a + 1) * 2
            with IfAll(computed > best):
                best.value = computed


messages = [str(w.message) for w in caught if issubclass(w.category, PyHTSWWarning)]
assert len(messages) == 1, messages
assert 'computed twice' in messages[0], messages[0]


with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    with Container():
        b = PlayerStat('wb').as_long()

        @function('NotReused')
        def not_reused() -> None:
            best = TemporaryStat().as_long().with_value(0)
            computed = TemporaryStat().as_long()
            computed.value = (b + 1) * 2
            with IfAll(computed > best):
                best.value = computed


assert not [w for w in caught if issubclass(w.category, PyHTSWWarning)], caught

print('test_select OK')
