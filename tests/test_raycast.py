"""create_raycast from pyhtsl.ext: hits, misses, headshots, piercing,
caps, conditions and the sender callback, driven through a multi-player
ExecutionContext with real geometry.

Geometry note: the caster's eyes sit `eye_height` (1.62) above their feet and a
target's torso is `torso_offset` (0.9) above theirs. A horizontal ray therefore
passes through a target whose feet are at the caster's-feet + 0.72, i.e. whose
torso is at eye level. The hitbox radius defaults to 1.0 block, so a target a
few blocks dead ahead is unambiguously hit while one several blocks to the side
is unambiguously missed — comfortably clear of the simulator's 3-decimal
rounding.
"""

from pyhtsl import (
    ExecutionContext,
    ExecutionPlayer,
    GlobalStat,
    IfAll,
    PlayerStat,
    disable_global_export,
)
from pyhtsl.actions.player_position_pitch import PlayerPositionPitch
from pyhtsl.actions.player_position_x import PlayerPositionX
from pyhtsl.actions.player_position_y import PlayerPositionY
from pyhtsl.actions.player_position_yaw import PlayerPositionYaw
from pyhtsl.actions.player_position_z import PlayerPositionZ
from pyhtsl.ext import create_raycast

disable_global_export()

# torso sits at the caster's eye level when a target's feet are here
TORSO_TO_EYE = 0.72


def place(
    player: ExecutionPlayer,
    x: float,
    y: float,
    z: float,
    *,
    yaw: float = 0.0,
    pitch: float = 0.0,
) -> None:
    player.put(PlayerPositionX, x)
    player.put(PlayerPositionY, y)
    player.put(PlayerPositionZ, z)
    player.put(PlayerPositionYaw, yaw)
    player.put(PlayerPositionPitch, pitch)


def registered_hits(ctx: ExecutionContext, prefix: str = 'rc/') -> int:
    """How many hits the last cast recorded (its `<prefix>hits` global)."""
    return int(ctx.get_raw(GlobalStat(f'{prefix}hits').as_long()))


# === Hit vs miss: only the player in the caster's line of sight is hit, and the
# caster never hits themselves. ===
caster = ExecutionPlayer('caster')
ahead = ExecutionPlayer('ahead')
beside = ExecutionPlayer('beside')
behind = ExecutionPlayer('behind')
was_hit = PlayerStat('was_hit').as_long()

with ExecutionContext(players=[caster, ahead, beside, behind]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, 0.0, 0.0, yaw=0.0)  # standing at origin, looking +Z
    place(ahead, 0.0, TORSO_TO_EYE, 5.0)  # dead ahead → hit
    place(beside, 5.0, 0.0, 5.0)  # well off to the side → miss
    place(behind, 0.0, TORSO_TO_EYE, -5.0)  # behind the caster → miss

    rc = create_raycast('Ray', on_hit_target=lambda: was_hit.set(1))
    rc.trigger()

assert int(ahead.get_raw(was_hit)) == 1, ahead.get_raw(was_hit)
assert int(beside.get_raw(was_hit)) == 0, beside.get_raw(was_hit)
assert int(behind.get_raw(was_hit)) == 0, behind.get_raw(was_hit)
assert int(caster.get_raw(was_hit)) == 0, caster.get_raw(was_hit)
assert registered_hits(ctx) == 1


# === Headshot vs bodyshot: the head band is 1.4–1.7 above a target's feet, so a
# target whose head is at eye level is a headshot and one whose torso is at eye
# level is a bodyshot. ===
caster = ExecutionPlayer('caster')
head = ExecutionPlayer('head')
body = ExecutionPlayer('body')
headshot_flag = PlayerStat('hs').as_long()

with ExecutionContext(players=[caster, head, body]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, 0.0, 0.0, yaw=0.0)
    place(head, 0.0, 0.0, 5.0)  # feet at caster level → head ~eye level → headshot
    place(body, 0.0, TORSO_TO_EYE, 8.0)  # torso at eye level → bodyshot

    rc = create_raycast(
        'Ray', on_hit_target=lambda res: headshot_flag.set(res.is_headshot)
    )
    rc.trigger()

assert int(head.get_raw(headshot_flag)) == 1, head.get_raw(headshot_flag)
assert int(body.get_raw(headshot_flag)) == 0, body.get_raw(headshot_flag)


# === headshots_only: a clean bodyshot is rejected entirely. ===
caster = ExecutionPlayer('caster')
body = ExecutionPlayer('body')
marker = PlayerStat('m').as_long()

with ExecutionContext(players=[caster, body]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, 0.0, 0.0, yaw=0.0)
    place(body, 0.0, TORSO_TO_EYE, 6.0)  # torso at eye level → bodyshot only

    rc = create_raycast('Ray', on_hit_target=lambda: marker.set(1), headshots_only=True)
    rc.trigger()

assert int(body.get_raw(marker)) == 0, body.get_raw(marker)
assert registered_hits(ctx) == 0


# === Pierce: by default every player along the ray is hit. ===
caster = ExecutionPlayer('caster')
t1 = ExecutionPlayer('t1')
t2 = ExecutionPlayer('t2')
t3 = ExecutionPlayer('t3')
marker = PlayerStat('m').as_long()

with ExecutionContext(players=[caster, t1, t2, t3]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, TORSO_TO_EYE, 0.0, yaw=0.0)
    place(t1, 0.0, TORSO_TO_EYE, 3.0)
    place(t2, 0.0, TORSO_TO_EYE, 6.0)
    place(t3, 0.0, TORSO_TO_EYE, 9.0)

    rc = create_raycast('Ray', on_hit_target=lambda: marker.set(1))
    rc.trigger()

assert registered_hits(ctx) == 3
for target in (t1, t2, t3):
    assert int(target.get_raw(marker)) == 1, (target.name, target.get_raw(marker))


# === max_hits caps the number of registered hits (first in execution order). ===
caster = ExecutionPlayer('caster')
t1 = ExecutionPlayer('t1')
t2 = ExecutionPlayer('t2')
marker = PlayerStat('m').as_long()

with ExecutionContext(players=[caster, t1, t2]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, TORSO_TO_EYE, 0.0, yaw=0.0)
    place(t1, 0.0, TORSO_TO_EYE, 3.0)
    place(t2, 0.0, TORSO_TO_EYE, 6.0)

    rc = create_raycast('Ray', on_hit_target=lambda: marker.set(1), max_hits=1)
    rc.trigger()

assert registered_hits(ctx) == 1
assert int(t1.get_raw(marker)) == 1, t1.get_raw(marker)
assert int(t2.get_raw(marker)) == 0, t2.get_raw(marker)


# === max_distance rejects an otherwise-aligned target that is too far. ===
caster = ExecutionPlayer('caster')
near = ExecutionPlayer('near')
far = ExecutionPlayer('far')
marker = PlayerStat('m').as_long()

with ExecutionContext(players=[caster, near, far]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, TORSO_TO_EYE, 0.0, yaw=0.0)
    place(near, 0.0, TORSO_TO_EYE, 5.0)
    place(far, 0.0, TORSO_TO_EYE, 30.0)

    rc = create_raycast('Ray', on_hit_target=lambda: marker.set(1), max_distance=10.0)
    rc.trigger()

assert int(near.get_raw(marker)) == 1, near.get_raw(marker)
assert int(far.get_raw(marker)) == 0, far.get_raw(marker)


# === conditions: only targets satisfying the extra condition are hit. ===
caster = ExecutionPlayer('caster')
friend = ExecutionPlayer('friend')
foe = ExecutionPlayer('foe')
marker = PlayerStat('m').as_long()
eligible = PlayerStat('eligible').as_long()

with ExecutionContext(players=[caster, friend, foe]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, TORSO_TO_EYE, 0.0, yaw=0.0)
    place(friend, 0.0, TORSO_TO_EYE, 3.0)
    place(foe, 0.0, TORSO_TO_EYE, 6.0)
    friend.put(eligible, 1)
    foe.put(eligible, 0)

    rc = create_raycast(
        'Ray',
        on_hit_target=lambda: marker.set(1),
        conditions=lambda: eligible == 1,
    )
    rc.trigger()

assert int(friend.get_raw(marker)) == 1, friend.get_raw(marker)
assert int(foe.get_raw(marker)) == 0, foe.get_raw(marker)


# === conditions also accepts a bare Condition (no callable wrapper). ===
caster = ExecutionPlayer('caster')
friend = ExecutionPlayer('friend')
foe = ExecutionPlayer('foe')
marker = PlayerStat('m').as_long()
eligible = PlayerStat('eligible').as_long()

with ExecutionContext(players=[caster, friend, foe]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, TORSO_TO_EYE, 0.0, yaw=0.0)
    place(friend, 0.0, TORSO_TO_EYE, 3.0)
    place(foe, 0.0, TORSO_TO_EYE, 6.0)
    friend.put(eligible, 1)
    foe.put(eligible, 0)

    rc = create_raycast(
        'Ray', on_hit_target=lambda: marker.set(1), conditions=eligible == 1
    )
    rc.trigger()

assert int(friend.get_raw(marker)) == 1, friend.get_raw(marker)
assert int(foe.get_raw(marker)) == 0, foe.get_raw(marker)


# === conditions also accepts an iterable of Conditions (all must hold). ===
caster = ExecutionPlayer('caster')
both = ExecutionPlayer('both')
one = ExecutionPlayer('one')
marker = PlayerStat('m').as_long()
flag_a = PlayerStat('flag_a').as_long()
flag_b = PlayerStat('flag_b').as_long()

with ExecutionContext(players=[caster, both, one]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, TORSO_TO_EYE, 0.0, yaw=0.0)
    place(both, 0.0, TORSO_TO_EYE, 3.0)
    place(one, 0.0, TORSO_TO_EYE, 6.0)
    both.put(flag_a, 1)
    both.put(flag_b, 1)
    one.put(flag_a, 1)
    one.put(flag_b, 0)

    rc = create_raycast(
        'Ray',
        on_hit_target=lambda: marker.set(1),
        conditions=[flag_a == 1, flag_b == 1],
    )
    rc.trigger()

assert int(both.get_raw(marker)) == 1, both.get_raw(marker)
assert int(one.get_raw(marker)) == 0, one.get_raw(marker)


# === The sender callback always runs (the caster cast the ray, he is never a
# target) and sees the total hit count. ===
caster = ExecutionPlayer('caster')
target = ExecutionPlayer('target')
notified = GlobalStat('notified').as_long()

with ExecutionContext(players=[caster, target]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, TORSO_TO_EYE, 0.0, yaw=0.0)
    place(target, 0.0, TORSO_TO_EYE, 4.0)

    def on_sender(res) -> None:
        with IfAll(res.hit_count > 0):
            notified.set(1)

    rc = create_raycast('Ray', on_hit_sender=on_sender)
    rc.trigger()

assert int(ctx.get_raw(notified)) == 1, ctx.get_raw(notified)


# === A miss casts cleanly: hit_count stays 0 and the sender callback's
# hit-gated branch does not fire. ===
caster = ExecutionPlayer('caster')
target = ExecutionPlayer('target')
notified = GlobalStat('notified').as_long()

with ExecutionContext(players=[caster, target]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, 0.0, 0.0, yaw=0.0)
    place(target, 20.0, 0.0, 0.0)  # straight to the side → miss

    def on_sender(res) -> None:
        with IfAll(res.hit_count > 0):
            notified.set(1)

    rc = create_raycast('Ray', on_hit_sender=on_sender)
    rc.trigger()

assert registered_hits(ctx) == 0
assert int(ctx.get_raw(notified)) == 0, ctx.get_raw(notified)


# === Rotated cast: facing -X (yaw 90) hits a target on the -X axis, not one on
# +Z — confirming the look vector tracks yaw. ===
caster = ExecutionPlayer('caster')
west = ExecutionPlayer('west')
south = ExecutionPlayer('south')
marker = PlayerStat('m').as_long()

with ExecutionContext(players=[caster, west, south]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, TORSO_TO_EYE, 0.0, yaw=90.0)  # facing -X
    place(west, -6.0, TORSO_TO_EYE, 0.0)  # along the look ray → hit
    place(south, 0.0, TORSO_TO_EYE, 6.0)  # 90° off → miss

    rc = create_raycast('Ray', on_hit_target=lambda: marker.set(1))
    rc.trigger()

assert int(west.get_raw(marker)) == 1, west.get_raw(marker)
assert int(south.get_raw(marker)) == 0, south.get_raw(marker)


# === Pitched cast: looking straight down (pitch 90) hits a target below. ===
caster = ExecutionPlayer('caster')
below = ExecutionPlayer('below')
ahead = ExecutionPlayer('ahead')
marker = PlayerStat('m').as_long()

with ExecutionContext(players=[caster, below, ahead]) as ctx:
    ctx.current_player = caster
    place(caster, 0.0, 10.0, 0.0, yaw=0.0, pitch=90.0)  # looking down
    place(below, 0.0, 5.0, 0.0)  # directly beneath → hit
    place(ahead, 0.0, 10.0, 6.0)  # straight ahead → miss

    rc = create_raycast('Ray', on_hit_target=lambda: marker.set(1))
    rc.trigger()

assert int(below.get_raw(marker)) == 1, below.get_raw(marker)
assert int(ahead.get_raw(marker)) == 0, ahead.get_raw(marker)


# === create_raycast builds exactly one Function. ===
with ExecutionContext(players=['caster']) as ctx:
    before = len(ctx.blocks)
    rc = create_raycast('SoloRay')
    after = len(ctx.blocks)

assert after - before == 1, (before, after)
