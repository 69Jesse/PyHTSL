from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from ..actions.conditional.statements import IfAll
from ..actions.create_function import create_function
from ..actions.exit_function import exit_function
from ..actions.function import Function
from ..actions.player_position_x import PlayerPositionX
from ..actions.player_position_y import PlayerPositionY
from ..actions.player_position_z import PlayerPositionZ
from ..actions.trigger_function import trigger_function
from ..expression.condition.condition import Condition
from ..stats.global_stat import GlobalStat
from ..stats.player_stat import PlayerStat
from ..utils.callback import call_with_optional_arg
from .look_vector import approximate_look_vector

__all__ = (
    'RaycastResult',
    'create_raycast',
)


# A single condition, a bunch of them, or a callable producing either — the
# callable form is handy when a condition must be rebuilt at emit time.
ConditionsArg = (
    Condition | Iterable[Condition] | Callable[[], Condition | Iterable[Condition]]
)
HitCallback = Callable[['RaycastResult'], Any] | Callable[[], Any]


@dataclass(frozen=True)
class RaycastResult:
    """A built raycast: its `Function`, a `trigger` to fire it, and the shared
    output GlobalStats.

    Fire the cast with `result.trigger()` (resets per-cast state and computes
    the look ray first), or re-run the bare function with
    `trigger_function(result.function)`.

    The output fields are GlobalStats, so the sender callback, every target
    callback, and the caller all read the same values. Inside a *target*
    callback `distance` / `is_headshot` describe that target's own hit; inside
    the *sender* callback they describe the most recently registered hit, and
    `hit_count` is the total number of players the ray passed through.
    """

    function: Function
    trigger: Callable[[], None]
    hit_count: GlobalStat
    is_headshot: GlobalStat
    distance: GlobalStat
    look_x: GlobalStat
    look_y: GlobalStat
    look_z: GlobalStat
    origin_x: GlobalStat
    origin_y: GlobalStat
    origin_z: GlobalStat


def _gather_conditions(conditions: 'ConditionsArg | None') -> list[Condition]:
    if conditions is None:
        return []
    if not isinstance(conditions, Condition) and callable(conditions):
        conditions = conditions()
    if isinstance(conditions, Condition):
        return [conditions]
    return list(conditions)


def create_raycast(
    name: str,
    *,
    stat_prefix: str = 'rc/',
    on_hit_target: HitCallback | None = None,
    on_hit_sender: HitCallback | None = None,
    conditions: ConditionsArg | None = None,
    hitbox_radius: float = 1.0,
    detect_headshots: bool = False,
    headshots_only: bool = False,
    max_hits: int | None = None,
    max_distance: float | None = None,
    eye_height: float = 1.62,
    torso_offset: float = 0.9,
    head_min_offset: float = 1.4,
    head_max_offset: float = 1.7,
) -> RaycastResult:
    """Build a player raycast and return a `RaycastResult`.

    The result bundles the created `Function` (`result.function`), the
    `trigger` that fires a cast (`result.trigger()`), and the output
    GlobalStats — all readable straight from the call site.

    Parameters
    ----------
    name:
        Name of the single `Function` that gets created.
    on_hit_target:
        Inlined for every player the ray hits, in *that player's* context.
        Receives the `RaycastResult` (or takes no argument). May contain its
        own conditionals.
    on_hit_sender:
        Inlined for the caster after the cast resolves, in the *caster's*
        context. Always runs (he cast the ray); branch on `result.hit_count`
        inside it if you only care about hits.
    conditions:
        Extra requirements a target must satisfy to count as hit, evaluated in
        the target's context (e.g. team checks, region checks, …). Accepts a
        single `Condition`, an iterable of them, or a callable returning either.
    hitbox_radius:
        Radius (blocks) of the spherical hitbox around each target's torso.
        Compared as a squared value, so 1.0 ≈ a forgiving full-body hit.
    detect_headshots:
        Compute `result.is_headshot` (head band `head_min_offset`..
        `head_max_offset` above the target's feet).
    headshots_only:
        Only register hits that land in the head band (implies
        `detect_headshots`).
    max_hits:
        Stop registering after this many players are hit (None = pierce
        everyone in the ray). With a cap, the *first* players in execution
        order win — that is not strictly the closest.
    max_distance:
        Reject hits whose distance along the ray exceeds this (None = no cap).
    eye_height / torso_offset / head_min_offset / head_max_offset:
        Geometry tuning (blocks).
    """

    def make_global(suffix: str, *, double: bool) -> GlobalStat:
        stat = GlobalStat(f'{stat_prefix}{suffix}')
        stat = stat.as_double() if double else stat.as_long()
        return stat.without_auto_unset()

    active = make_global('active', double=False)
    dist2 = make_global('dist2', double=True)
    look_x = make_global('look/x', double=True)
    look_y = make_global('look/y', double=True)
    look_z = make_global('look/z', double=True)
    pos_x = make_global('pos/x', double=True)
    pos_y = make_global('pos/y', double=True)
    pos_z = make_global('pos/z', double=True)
    hits = make_global('hits', double=False)
    length = make_global('length', double=True)
    headshot = make_global('headshot', double=False)

    def player_double(suffix: str) -> PlayerStat:
        return PlayerStat(f'{stat_prefix}{suffix}').as_double().without_auto_unset()

    def player_long(suffix: str) -> PlayerStat:
        return PlayerStat(f'{stat_prefix}{suffix}').as_long().without_auto_unset()

    @create_function(name)
    def raycast_function() -> None:
        # --- ORIGIN: the caster. Fan the ray out to everyone but himself
        # (the cooldown from his own entry call excludes him), then bail. ---
        with IfAll(active == 0):
            active.value = 1
            trigger_function(result.function, True)
            active.value = 0
            exit_function()

        # --- TARGET: this player is being tested against the caster's ray. ---
        offset_x = player_double('offset/x')
        offset_y = player_double('offset/y')
        offset_z = player_double('offset/z')
        ray_dist = player_double('raydist')
        perp2 = player_double('perp2')
        t1 = player_double('t1')
        t2 = player_double('t2')
        my_hit = player_long('myhit')
        my_headshot = player_long('myheadshot')

        # offset = (target torso) - (ray origin)
        offset_x.value = PlayerPositionX
        offset_x.value -= pos_x
        offset_y.value = PlayerPositionY
        offset_y.value += torso_offset
        offset_y.value -= pos_y
        offset_z.value = PlayerPositionZ
        offset_z.value -= pos_z

        # ray_dist = offset · look  (signed distance along the unit ray)
        t1.value = offset_x
        t1.value *= look_x
        ray_dist.value = t1
        t1.value = offset_y
        t1.value *= look_y
        ray_dist.value += t1
        t1.value = offset_z
        t1.value *= look_z
        ray_dist.value += t1

        # perp2 = |offset × look|²  (squared perpendicular distance to the ray)
        perp2.value = 0.0
        # (offsetY*lookZ - offsetZ*lookY)²
        t1.value = offset_y
        t1.value *= look_z
        t2.value = offset_z
        t2.value *= look_y
        t1.value -= t2
        t1.value *= t1
        perp2.value += t1
        # (offsetZ*lookX - offsetX*lookZ)²
        t1.value = offset_z
        t1.value *= look_x
        t2.value = offset_x
        t2.value *= look_z
        t1.value -= t2
        t1.value *= t1
        perp2.value += t1
        # (offsetX*lookY - offsetY*lookX)²
        t1.value = offset_x
        t1.value *= look_y
        t2.value = offset_y
        t2.value *= look_x
        t1.value -= t2
        t1.value *= t1
        perp2.value += t1

        # Hit test: close enough to the ray AND in front of the caster.
        hit_conditions: list[Condition] = [perp2 <= dist2, ray_dist >= 0.0]
        if max_distance is not None:
            hit_conditions.append(ray_dist <= max_distance)
        hit_conditions.extend(_gather_conditions(conditions))

        my_hit.value = 0
        with IfAll(*hit_conditions):
            my_hit.value = 1

        # headshots_only needs the head band too, so it implies detection.
        if detect_headshots or headshots_only:
            hit_y = player_double('hity')
            head_min = player_double('headmin')
            head_max = player_double('headmax')

            hit_y.value = ray_dist
            hit_y.value *= look_y
            hit_y.value += pos_y
            head_min.value = PlayerPositionY
            head_min.value += head_min_offset
            head_max.value = PlayerPositionY
            head_max.value += head_max_offset

            my_headshot.value = 0
            with IfAll(my_hit == 1, hit_y >= head_min, hit_y <= head_max):
                my_headshot.value = 1
            if headshots_only:
                with IfAll(my_hit == 1, my_headshot == 0):
                    my_hit.value = 0

        if max_hits is not None:
            with IfAll(my_hit == 1, hits >= max_hits):
                my_hit.value = 0

        # Not a hit → stop here. Everything past this point is the hit path at
        # top level, so the target callback is free to use its own conditionals.
        with IfAll(my_hit == 0):
            exit_function()

        hits.value += 1
        length.value = ray_dist
        headshot.value = my_headshot

        if on_hit_target is not None:
            call_with_optional_arg(on_hit_target, result, noun='on_hit_target')

    def trigger() -> None:
        # Reset per-cast outputs.
        dist2.value = float(hitbox_radius) * float(hitbox_radius)
        hits.value = 0
        length.value = 0.0
        headshot.value = 0

        # Look direction from the caster's eyes.
        approximate_look_vector(
            assign_to_x=look_x,
            assign_to_y=look_y,
            assign_to_z=look_z,
        )

        # Ray origin at the caster's eyes.
        pos_x.value = PlayerPositionX
        pos_y.value = PlayerPositionY
        pos_y.value += eye_height
        pos_z.value = PlayerPositionZ

        # Launch: the caster runs as the origin, which fans out to everyone else.
        active.value = 0
        trigger_function(raycast_function)

        if on_hit_sender is not None:
            call_with_optional_arg(on_hit_sender, result, noun='on_hit_sender')

    result = RaycastResult(
        function=raycast_function,
        trigger=trigger,
        hit_count=hits,
        is_headshot=headshot,
        distance=length,
        look_x=look_x,
        look_y=look_y,
        look_z=look_z,
        origin_x=pos_x,
        origin_y=pos_y,
        origin_z=pos_z,
    )
    return result
