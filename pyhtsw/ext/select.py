from collections.abc import Callable, Sequence

from pyhtsw.actions.flow import IfAll
from pyhtsw.checkable import Checkable
from pyhtsw.editable import Editable, HousingType
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.ext.array_read_write import MaybeSequence, into_sequence
from pyhtsw.ext.geometry import Point, distance_squared, player_position
from pyhtsw.internal_type import InternalType
from pyhtsw.stats.temporary_stat import TemporaryStat

__all__ = (
    'nearest_position',
    'select_max',
    'select_min',
)

type Key[T] = Callable[[T], Checkable | HousingType]
type Payload[T] = Callable[[T], MaybeSequence[Checkable | HousingType]]
type Where[T] = Callable[[T], MaybeSequence[Condition] | None]

_LIMIT = 1 << 62


def _select[T](
    candidates: Sequence[T],
    *,
    key: Key[T],
    payload: Payload[T] | None,
    output: MaybeSequence[Editable],
    where: Where[T] | None,
    keep_greater: bool,
    numeric_type: InternalType,
    seed: Checkable | HousingType | None,
    key_stat: TemporaryStat | None,
) -> TemporaryStat:
    outputs = list(into_sequence(output))
    best = TemporaryStat()._as_type(numeric_type)
    if seed is None:
        seed = -_LIMIT if keep_greater else _LIMIT
        if numeric_type is InternalType.DOUBLE:
            seed = float(seed)
    best.value = seed
    # The key is materialised before it is compared, so storing it costs one
    # action instead of a second flatten. A caller whose key already writes a
    # stat passes it as `key_stat`, and the assignment short-circuits.
    current = (
        key_stat
        if key_stat is not None
        else TemporaryStat()._as_type(
            numeric_type,
        )
    )

    for candidate in candidates:
        current.value = key(candidate)
        guards = where(candidate) if where is not None else None
        conditions = list(into_sequence(guards)) if guards is not None else []
        better = current > best if keep_greater else current < best
        with IfAll(*conditions, better):
            best.value = current
            if payload is not None:
                values = list(into_sequence(payload(candidate)))
                for target, value in zip(outputs, values, strict=True):
                    target.value = value
    return best


def select_min[T](
    candidates: Sequence[T],
    *,
    key: Key[T],
    output: MaybeSequence[Editable] = (),
    payload: Payload[T] | None = None,
    where: Where[T] | None = None,
    numeric_type: InternalType = InternalType.LONG,
    seed: Checkable | HousingType | None = None,
    key_stat: TemporaryStat | None = None,
) -> TemporaryStat:
    """Walk `candidates` once and keep the smallest `key`, copying that
    candidate's `payload` into `output`. Returns the winning key."""
    return _select(
        candidates,
        key=key,
        payload=payload,
        output=output,
        where=where,
        keep_greater=False,
        numeric_type=numeric_type,
        seed=seed,
        key_stat=key_stat,
    )


def select_max[T](
    candidates: Sequence[T],
    *,
    key: Key[T],
    output: MaybeSequence[Editable] = (),
    payload: Payload[T] | None = None,
    where: Where[T] | None = None,
    numeric_type: InternalType = InternalType.LONG,
    seed: Checkable | HousingType | None = None,
    key_stat: TemporaryStat | None = None,
) -> TemporaryStat:
    """`select_min`, keeping the largest key instead."""
    return _select(
        candidates,
        key=key,
        payload=payload,
        output=output,
        where=where,
        keep_greater=True,
        numeric_type=numeric_type,
        seed=seed,
        key_stat=key_stat,
    )


def nearest_position(
    candidates: Sequence[Point],
    *,
    output: MaybeSequence[Editable],
    to: Point | None = None,
    within: float | None = None,
    where: Where[Point] | None = None,
    if_none: MaybeSequence[HousingType] | Callable[[], None] | None = None,
) -> TemporaryStat:
    """The candidate closest to `to` (the player by default), written into
    `output`. Returns the winning squared distance."""
    target = player_position() if to is None else to
    outputs = list(into_sequence(output))
    scratch = [TemporaryStat()._as_type(InternalType.DOUBLE) for _ in outputs]
    current = TemporaryStat().as_double()
    axis = TemporaryStat().as_double()

    best = select_min(
        candidates,
        key=lambda candidate: distance_squared(
            candidate,
            target,
            into=current,
            axis=axis,
        ),
        payload=lambda candidate: list(candidate)[: len(outputs)],
        output=scratch,
        where=where,
        numeric_type=InternalType.DOUBLE,
        key_stat=current,
    )

    if callable(if_none):
        if_none()
    elif if_none is not None:
        for target_stat, value in zip(
            outputs,
            into_sequence(if_none),
            strict=True,
        ):
            target_stat.value = value
    limit = float(_LIMIT) if within is None else within * within
    with IfAll(best <= limit):
        for target_stat, value in zip(outputs, scratch, strict=True):
            target_stat.value = value
    return best
