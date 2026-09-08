import math
from collections.abc import Callable, Sequence
from types import EllipsisType
from typing import Literal

from pyhtsw.actions.flow import Else, IfAll
from pyhtsw.checkable import Checkable
from pyhtsw.editable import Editable, HousingType
from pyhtsw.ext.array_read_write import MaybeSequence, assert_same_widths, into_sequence
from pyhtsw.helpers import chunked
from pyhtsw.stats.stat import Stat
from pyhtsw.stats.temporary_stat import TemporaryStat

type Factory[T] = Callable[[int], T]
type MaybeFactory[T] = T | Factory[T]


type OnOverflow = Literal['ignore', 'override_oldest', 'override_newest']

type IfEmptyInt = Checkable | int | Callable[[], None] | None
type IfEmptyAny = Checkable | HousingType | Callable[[], None] | None
type IfPresent = Callable[[], None] | None


def _into_factory(item: MaybeFactory[Stat]) -> Factory[Stat]:
    if callable(item):
        return item
    return lambda _i: item


def _to_signed_long(x: int) -> int:
    return x - (1 << 64) if x >= (1 << 63) else x


class _BitPackedBase:
    holders: Sequence[Sequence[Stat]]
    counter: Stat
    most: int
    real_capacity: int
    on_overflow: OnOverflow
    if_empty: IfEmptyInt
    if_present: IfPresent

    @property
    def bits(self) -> int:
        return self.most.bit_length()

    @property
    def per_holder_capacity(self) -> int:
        return 64 // self.bits

    @property
    def width(self) -> int:
        # `holders` is column-major here: one group per width-position.
        return len(self.holders)

    def __init__(
        self,
        *,
        holder: MaybeSequence[MaybeFactory[Stat]],
        counter: Stat,
        most: int,
        capacity: int | None = None,
        capacity_is_exact: bool = False,
        on_overflow: OnOverflow = 'ignore',
        if_empty: IfEmptyInt = -1,
        if_present: IfPresent = None,
    ) -> None:
        assert most >= 1
        bits = most.bit_length()
        per_holder_capacity = 64 // bits
        if per_holder_capacity <= 1:
            raise ValueError(
                f'{type(self).__name__}: `most`={most} needs {bits} bits per '
                f'value, but this only supports up to 63 bits',
            )

        if capacity is None:
            n_holders = 1
            real_capacity = per_holder_capacity
        else:
            if capacity <= 0:
                raise ValueError(
                    f'{type(self).__name__}: capacity must be positive, got {capacity}',
                )
            n_holders = math.ceil(capacity / per_holder_capacity)
            real_capacity = (
                capacity if capacity_is_exact else n_holders * per_holder_capacity
            )

        self.on_overflow = on_overflow
        self._validate_overflow_capacity(
            real_capacity=real_capacity,
            n_holders=n_holders,
            per_holder_capacity=per_holder_capacity,
        )

        per_position_factories = [_into_factory(item) for item in into_sequence(holder)]
        if not per_position_factories:
            raise ValueError(f'{type(self).__name__}: at least one holder is required')

        groups: list[tuple[Stat, ...]] = []
        for factory in per_position_factories:
            groups.append(tuple(factory(i) for i in range(n_holders)))

        seen: list[Stat] = []
        for group in groups:
            for stat in group:
                for prior in seen:
                    if stat.is_same_stat(prior):
                        raise ValueError(
                            f'{type(self).__name__}: holder stat {stat!r} is '
                            f'duplicated. Pass a factory like '
                            f'`lambda i: PlayerStat(f"name{{i}}")` for stacks '
                            f'that need multiple holders ({n_holders} required '
                            f'for capacity {real_capacity}).',
                        )
                seen.append(stat)

        self.holders = groups
        self.counter = counter
        self.most = most
        self.real_capacity = real_capacity
        self.if_empty = if_empty
        self.if_present = if_present

    def _validate_overflow_capacity(
        self,
        *,
        real_capacity: int,
        n_holders: int,
        per_holder_capacity: int,
    ) -> None:
        pass

    def _validate_front_override_capacity(
        self,
        *,
        real_capacity: int,
        n_holders: int,
        per_holder_capacity: int,
    ) -> None:
        # Pushing the front drops the top slot of the top holder, so an
        # `override_oldest` capacity that stops short of that slot would evict
        # a value that is still inside the container.
        if (
            self.on_overflow == 'override_oldest'
            and real_capacity != n_holders * per_holder_capacity
        ):
            raise ValueError(
                f'{type(self).__name__}: on_overflow="override_oldest" '
                f'requires real capacity ({real_capacity}) to equal n_holders '
                f'* per_holder_capacity ({n_holders} * {per_holder_capacity} '
                f'= {n_holders * per_holder_capacity}). Either drop '
                f'capacity_is_exact or pick a capacity that is a '
                f'multiple of {per_holder_capacity}.',
            )

    def _check_value(self, v: Checkable | int) -> None:
        if isinstance(v, int) and (v < 0 or v > self.most):
            raise ValueError(
                f'{type(self).__name__}: value {v} out of range [0, {self.most}]',
            )

    def _normalize_values(
        self,
        value: MaybeSequence[Checkable | int],
        *,
        label: str,
    ) -> list[Checkable | int]:
        values = list(into_sequence(value))
        if len(values) != self.width:
            raise ValueError(
                f'{type(self).__name__}.{label}: got {len(values)} value(s), '
                f'expected {self.width} (one per width-position)',
            )
        for v in values:
            self._check_value(v)
        return values

    def _normalize_outputs(
        self,
        output: MaybeSequence[Editable],
        *,
        label: str,
    ) -> list[Editable]:
        outputs = list(into_sequence(output))
        if len(outputs) != self.width:
            raise ValueError(
                f'{type(self).__name__}.{label}: got {len(outputs)} output(s), '
                f'expected {self.width} (one per width-position)',
            )
        return outputs

    def _cascade_right(self, outputs: Sequence[Editable] | None) -> None:
        bits = self.bits
        cap = self.per_holder_capacity
        slot_mask = (1 << bits) - 1
        top_shift = (cap - 1) * bits
        n = len(self.holders[0])

        for w in range(self.width):
            column = self.holders[w]
            if outputs is not None:
                outputs[w].value = column[0] & slot_mask
            for h in range(n):
                if h + 1 < n:
                    carry_up = (column[h + 1] & slot_mask) << top_shift
                    # Logical (`>>>=`) so bit 63 is filled with 0 instead
                    # of being sign-extended into the next-to-pop slot.
                    column[h].logical_rshift(bits).write()
                    column[h].value |= carry_up
                else:
                    column[h].logical_rshift(bits).write()

    def _drain_front(
        self,
        outputs: Sequence[Editable],
        *,
        if_empty: IfEmptyInt | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        if isinstance(if_empty, EllipsisType):
            if_empty = self.if_empty
        if isinstance(if_present, EllipsisType):
            if_present = self.if_present

        with chunked(IfAll(self.counter > 0)):
            self._cascade_right(outputs)
            if if_present is not None:
                if_present()
            self.counter.value -= 1
        if if_empty is not None:
            with Else:
                if callable(if_empty):
                    if_empty()
                else:
                    for o in outputs:
                        o.value = if_empty

    def _extract_at_back(
        self,
        last: Editable,
        holder_index: int,
        outputs: Sequence[Editable],
    ) -> None:
        bits = self.bits
        base = holder_index * self.per_holder_capacity
        slot_mask = (1 << bits) - 1
        for w in range(self.width):
            column = self.holders[w][holder_index]
            shift = (last - base) * bits if base else last * bits
            outputs[w].value = column.logical_rshift(shift)
            outputs[w].value &= slot_mask
            column.value -= outputs[w] << shift

    def _drain_back(
        self,
        outputs: Sequence[Editable],
        *,
        if_empty: IfEmptyInt | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        if isinstance(if_empty, EllipsisType):
            if_empty = self.if_empty
        if isinstance(if_present, EllipsisType):
            if_present = self.if_present

        cap = self.per_holder_capacity
        n = len(self.holders[0])
        last = TemporaryStat().as_long()
        last.value = self.counter
        last.value -= 1

        if n == 1:
            with chunked(IfAll(self.counter > 0)):
                self._extract_at_back(last, 0, outputs)
                if if_present is not None:
                    if_present()
                self.counter.value -= 1
        else:
            for h in range(n):
                upper = min((h + 1) * cap, self.real_capacity)
                with chunked(IfAll(last >= h * cap, last < upper)):
                    self._extract_at_back(last, h, outputs)
            with chunked(IfAll(self.counter > 0)):
                if if_present is not None:
                    if_present()
                self.counter.value -= 1
        if if_empty is not None:
            with Else:
                if callable(if_empty):
                    if_empty()
                else:
                    for o in outputs:
                        o.value = if_empty

    def _push_front(self, value: MaybeSequence[Checkable | int]) -> None:
        values = self._normalize_values(value, label='add')

        bits = self.bits
        cap = self.per_holder_capacity
        slot_mask = (1 << bits) - 1
        top_shift = (cap - 1) * bits
        n = len(self.holders[0])
        needs_mask = cap * bits < 64
        holder_mask = (1 << (cap * bits)) - 1 if needs_mask else 0

        def cascade_up_and_insert() -> None:
            for w in range(self.width):
                column = self.holders[w]
                # Read each holder's top slot before the lower holder gets
                # shifted in the next iteration.
                for h in range(n - 1, 0, -1):
                    carry = (column[h - 1] >> top_shift) & slot_mask
                    column[h].value <<= bits
                    if needs_mask:
                        column[h].value &= holder_mask
                    column[h].value += carry
                column[0].value <<= bits
                if needs_mask:
                    column[0].value &= holder_mask
                column[0].value += values[w]

        if self.on_overflow == 'ignore':
            with chunked(IfAll(self.counter < self.real_capacity)):
                cascade_up_and_insert()
                self.counter.value += 1
        elif self.on_overflow == 'override_oldest':
            cascade_up_and_insert()
            with IfAll(self.counter < self.real_capacity):
                self.counter.value += 1
        else:
            with chunked(IfAll(self.counter < self.real_capacity)):
                cascade_up_and_insert()
                self.counter.value += 1
            with Else:
                for w in range(self.width):
                    self.holders[w][0].value &= ~slot_mask
                    self.holders[w][0].value += values[w]

    def _push_back(self, value: MaybeSequence[Checkable | int]) -> None:
        values = self._normalize_values(value, label='add')

        if self.on_overflow == 'override_oldest':
            with chunked(IfAll(self.counter == self.real_capacity)):
                self._cascade_right(None)
                self.counter.value -= 1
        elif self.on_overflow == 'override_newest':
            with IfAll(self.counter == self.real_capacity):
                self._overwrite_back(values)

        self._insert_at_back(values)

    def _insert_at_back(self, values: list[Checkable | int]) -> None:
        cap = self.per_holder_capacity
        bits = self.bits
        n = len(self.holders[0])

        for h in range(n - 1, -1, -1):
            upper = min((h + 1) * cap, self.real_capacity)
            # The lower bound is vacuous for the first holder; passing the
            # bare Python `False` the old `and` produced would silently make
            # the conditional never fire on a signature change.
            lower = [self.counter >= h * cap] if h != 0 else []
            with IfAll(
                *lower,
                self.counter < upper,
            ):
                shift_amount = TemporaryStat().as_long()
                shift_amount.value = (self.counter - h * cap) * bits
                for w in range(self.width):
                    self.holders[w][h].value |= values[w] << shift_amount
                self.counter.value += 1

    def _overwrite_back(self, values: list[Checkable | int]) -> None:
        cap = self.per_holder_capacity
        bits = self.bits
        slot_mask = (1 << bits) - 1
        target_pos = self.real_capacity - 1
        target_h = target_pos // cap
        shift = (target_pos % cap) * bits
        slot_mask_shifted = _to_signed_long(slot_mask << shift)

        for w in range(self.width):
            target = self.holders[w][target_h]
            target.value ^= target & slot_mask_shifted
            target.value += values[w] << shift


class IntStack(_BitPackedBase):
    def _validate_overflow_capacity(
        self,
        *,
        real_capacity: int,
        n_holders: int,
        per_holder_capacity: int,
    ) -> None:
        self._validate_front_override_capacity(
            real_capacity=real_capacity,
            n_holders=n_holders,
            per_holder_capacity=per_holder_capacity,
        )

    def push(self, value: MaybeSequence[Checkable | int]) -> None:
        self._push_front(value)

    def pop(
        self,
        *,
        output: MaybeSequence[Editable],
        if_empty: IfEmptyInt | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        self._drain_front(
            self._normalize_outputs(output, label='remove'),
            if_empty=if_empty,
            if_present=if_present,
        )


class IntQueue(_BitPackedBase):
    def push(self, value: MaybeSequence[Checkable | int]) -> None:
        self._push_back(value)

    def pop(
        self,
        *,
        output: MaybeSequence[Editable],
        if_empty: IfEmptyInt | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        self._drain_front(
            self._normalize_outputs(output, label='remove'),
            if_empty=if_empty,
            if_present=if_present,
        )


class IntDeque(_BitPackedBase):
    """A bit-packed double-ended queue.

    Every operation is a handful of shift/mask actions, because a variable
    shift distance is dynamic addressing - the thing a slot array can never
    do. `on_overflow` reads relative to the end being pushed: the "oldest"
    value is the one at the far end.
    """

    def _validate_overflow_capacity(
        self,
        *,
        real_capacity: int,
        n_holders: int,
        per_holder_capacity: int,
    ) -> None:
        self._validate_front_override_capacity(
            real_capacity=real_capacity,
            n_holders=n_holders,
            per_holder_capacity=per_holder_capacity,
        )

    def push_front(self, value: MaybeSequence[Checkable | int]) -> None:
        self._push_front(value)

    def push_back(self, value: MaybeSequence[Checkable | int]) -> None:
        self._push_back(value)

    def pop_front(
        self,
        *,
        output: MaybeSequence[Editable],
        if_empty: IfEmptyInt | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        self._drain_front(
            self._normalize_outputs(output, label='remove'),
            if_empty=if_empty,
            if_present=if_present,
        )

    def pop_back(
        self,
        *,
        output: MaybeSequence[Editable],
        if_empty: IfEmptyInt | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        self._drain_back(
            self._normalize_outputs(output, label='remove'),
            if_empty=if_empty,
            if_present=if_present,
        )


class _SlotContainerBase:
    holders: Sequence[Sequence[Stat]]
    counter: Stat
    on_overflow: OnOverflow
    if_empty: IfEmptyAny
    if_present: IfPresent

    @property
    def capacity(self) -> int:
        return len(self.holders)

    @property
    def width(self) -> int:
        return len(self.holders[0])

    def __init__(
        self,
        *,
        holders: Sequence[MaybeSequence[Stat]],
        counter: Stat,
        on_overflow: OnOverflow = 'ignore',
        if_empty: IfEmptyAny = None,
        if_present: IfPresent = None,
    ) -> None:
        if not holders:
            raise ValueError(f'{type(self).__name__}: holders must be non-empty')

        groups = [tuple(into_sequence(g)) for g in holders]
        assert_same_widths(groups)

        seen: list[Stat] = []
        for group in groups:
            for stat in group:
                for prior in seen:
                    if stat.is_same_stat(prior):
                        raise ValueError(
                            f'{type(self).__name__}: holder stat {stat!r} '
                            f'is duplicated. Each slot needs its own Stat.',
                        )
                seen.append(stat)

        self.holders = groups
        self.counter = counter
        self.on_overflow = on_overflow
        self.if_empty = if_empty
        self.if_present = if_present

    def _normalize_values(
        self,
        value: MaybeSequence[Checkable | HousingType],
        *,
        label: str,
    ) -> list[Checkable | HousingType]:
        if isinstance(value, str):
            values: list[Checkable | HousingType] = [value]
        else:
            values = list(into_sequence(value))
        if len(values) != self.width:
            raise ValueError(
                f'{type(self).__name__}.{label}: got {len(values)} value(s), '
                f'expected {self.width} (one per width-position)',
            )
        return values

    def _normalize_outputs(
        self,
        output: MaybeSequence[Editable],
        *,
        label: str,
    ) -> list[Editable]:
        outputs = list(into_sequence(output))
        if len(outputs) != self.width:
            raise ValueError(
                f'{type(self).__name__}.{label}: got {len(outputs)} output(s), '
                f'expected {self.width} (one per width-position)',
            )
        return outputs

    def _write_at_slot(
        self,
        slot_index: int,
        values: Sequence[Checkable | HousingType],
    ) -> None:
        for w in range(self.width):
            self.holders[slot_index][w].value = values[w]

    def _shift_up(self) -> None:
        for i in range(self.capacity - 1, 0, -1):
            for w in range(self.width):
                self.holders[i][w].value = self.holders[i - 1][w]

    def _shift_down(self, outputs: Sequence[Editable] | None) -> None:
        if outputs is not None:
            for w in range(self.width):
                outputs[w].value = self.holders[0][w]
        for i in range(self.capacity - 1):
            for w in range(self.width):
                self.holders[i][w].value = self.holders[i + 1][w]

    def _drain_front(
        self,
        outputs: Sequence[Editable],
        *,
        if_empty: IfEmptyAny | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        if isinstance(if_empty, EllipsisType):
            if_empty = self.if_empty
        if isinstance(if_present, EllipsisType):
            if_present = self.if_present

        with chunked(IfAll(self.counter > 0)):
            self._shift_down(outputs)
            if if_present is not None:
                if_present()
            self.counter.value -= 1
        if if_empty is not None:
            with Else:
                if callable(if_empty):
                    if_empty()
                else:
                    for o in outputs:
                        o.value = if_empty

    def _push_front(self, value: MaybeSequence[Checkable | HousingType]) -> None:
        values = self._normalize_values(value, label='add')

        if self.on_overflow == 'ignore':
            with chunked(IfAll(self.counter < self.capacity)):
                self._shift_up()
                self._write_at_slot(0, values)
                self.counter.value += 1
        elif self.on_overflow == 'override_oldest':
            self._shift_up()
            self._write_at_slot(0, values)
            with IfAll(self.counter < self.capacity):
                self.counter.value += 1
        else:
            with chunked(IfAll(self.counter < self.capacity)):
                self._shift_up()
                self._write_at_slot(0, values)
                self.counter.value += 1
            with Else:
                self._write_at_slot(0, values)

    def _push_back(self, value: MaybeSequence[Checkable | HousingType]) -> None:
        values = self._normalize_values(value, label='add')

        if self.on_overflow == 'override_oldest':
            with chunked(IfAll(self.counter == self.capacity)):
                self._shift_down(None)
                self.counter.value -= 1

        # An add is a write at slot `counter`, so when the holders take
        # array_write's fast path (long stats named in an arithmetic run) the
        # per-slot conditional cascade collapses into the composed write plus
        # one counter guard.
        from pyhtsw.ext.array_read_write import _fast_write_plan, array_write

        if (
            _fast_write_plan(
                items=self.holders,
                n=self.capacity,
                width=self.width,
            )
            is not None
        ):
            if self.on_overflow == 'override_oldest':
                # The shift above put counter back in range when full.
                index: Editable = self.counter  # type: ignore[assignment]
            else:
                clamp = TemporaryStat().as_long()
                index_stat = TemporaryStat().as_long()
                clamp.value = self.counter
                clamp.value //= self.capacity
                if self.on_overflow == 'ignore':
                    # A full queue steers the index to -1, which misses every
                    # composed key.
                    clamp.value *= self.capacity + 1
                # else: full steers to capacity - 1 (override_newest).
                index_stat.value = self.counter
                index_stat.value -= clamp
                index = index_stat
            array_write(items=self.holders, index=index, input=values)
            if self.on_overflow == 'override_oldest':
                self.counter.value += 1
            else:
                with IfAll(self.counter < self.capacity):
                    self.counter.value += 1
            return

        if self.on_overflow == 'override_newest':
            with IfAll(self.counter == self.capacity):
                self._write_at_slot(self.capacity - 1, values)

        for i in range(self.capacity - 1, -1, -1):
            with IfAll(self.counter == i):
                self._write_at_slot(i, values)
                self.counter.value += 1

    def _drain_back(
        self,
        outputs: Sequence[Editable],
        *,
        if_empty: IfEmptyAny | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        if isinstance(if_empty, EllipsisType):
            if_empty = self.if_empty
        if isinstance(if_present, EllipsisType):
            if_present = self.if_present

        from pyhtsw.ext.array_read_write import _detect_pattern, array_read

        last = TemporaryStat().as_long()
        last.value = self.counter
        last.value -= 1

        composed = _detect_pattern(self.holders) is not None
        if composed:
            with chunked(IfAll(self.counter > 0)):
                array_read(items=self.holders, index=last, output=outputs)
                if if_present is not None:
                    if_present()
                self.counter.value -= 1
        else:
            for i in range(self.capacity):
                with chunked(IfAll(self.counter == i + 1)):
                    for w in range(self.width):
                        outputs[w].value = self.holders[i][w]
            with chunked(IfAll(self.counter > 0)):
                if if_present is not None:
                    if_present()
                self.counter.value -= 1
        if if_empty is not None:
            with Else:
                if callable(if_empty):
                    if_empty()
                else:
                    for o in outputs:
                        o.value = if_empty


class Stack(_SlotContainerBase):
    def push(self, value: MaybeSequence[Checkable | HousingType]) -> None:
        self._push_front(value)

    def pop(
        self,
        *,
        output: MaybeSequence[Editable],
        if_empty: IfEmptyAny | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        self._drain_front(
            self._normalize_outputs(output, label='remove'),
            if_empty=if_empty,
            if_present=if_present,
        )


class Queue(_SlotContainerBase):
    def push(self, value: MaybeSequence[Checkable | HousingType]) -> None:
        self._push_back(value)

    def pop(
        self,
        *,
        output: MaybeSequence[Editable],
        if_empty: IfEmptyAny | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        self._drain_front(
            self._normalize_outputs(output, label='remove'),
            if_empty=if_empty,
            if_present=if_present,
        )


class Deque(_SlotContainerBase):
    """A double-ended queue over one Stat per slot.

    Holds anything a Stat can - strings and doubles included - at the cost of
    an O(capacity) shift on either front operation. `pop_back` moves nothing,
    and `push_back` inherits `array_write`'s composed-name fast path, so the
    back is the cheap end. `on_overflow` reads relative to the end being
    pushed: the "oldest" value is the one at the far end.
    """

    def push_front(self, value: MaybeSequence[Checkable | HousingType]) -> None:
        self._push_front(value)

    def push_back(self, value: MaybeSequence[Checkable | HousingType]) -> None:
        self._push_back(value)

    def pop_front(
        self,
        *,
        output: MaybeSequence[Editable],
        if_empty: IfEmptyAny | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        self._drain_front(
            self._normalize_outputs(output, label='remove'),
            if_empty=if_empty,
            if_present=if_present,
        )

    def pop_back(
        self,
        *,
        output: MaybeSequence[Editable],
        if_empty: IfEmptyAny | EllipsisType = ...,
        if_present: IfPresent | EllipsisType = ...,
    ) -> None:
        self._drain_back(
            self._normalize_outputs(output, label='remove'),
            if_empty=if_empty,
            if_present=if_present,
        )
