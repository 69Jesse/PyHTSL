import math
from collections.abc import Callable, Sequence
from types import EllipsisType
from typing import Literal

from pyhtsl.stats.stat import Stat

from ..actions.conditional.statements import Else, IfAll
from ..checkable import Checkable
from ..editable import Editable, HousingType
from ..helpers import chunked
from .cheap_read_write import MaybeSequence, assert_same_widths, into_sequence

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
    width: int

    @property
    def bits(self) -> int:
        return self.most.bit_length()

    @property
    def per_holder_capacity(self) -> int:
        return 64 // self.bits

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
                f'value, but this only supports up to 63 bits'
            )

        if capacity is None:
            n_holders = 1
            real_capacity = per_holder_capacity
        else:
            if capacity <= 0:
                raise ValueError(
                    f'{type(self).__name__}: capacity must be positive, got {capacity}'
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
        width = len(per_position_factories)

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
                            f'for capacity {real_capacity}).'
                        )
                seen.append(stat)

        self.holders = groups
        self.counter = counter
        self.most = most
        self.real_capacity = real_capacity
        self.if_empty = if_empty
        self.if_present = if_present
        self.width = width

    def _validate_overflow_capacity(
        self,
        *,
        real_capacity: int,
        n_holders: int,
        per_holder_capacity: int,
    ) -> None:
        pass

    def _check_value(self, v: Checkable | int) -> None:
        if isinstance(v, int) and (v < 0 or v > self.most):
            raise ValueError(
                f'{type(self).__name__}: value {v} out of range [0, {self.most}]'
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
                f'expected {self.width} (one per width-position)'
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
                f'expected {self.width} (one per width-position)'
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


class IntStack(_BitPackedBase):
    def _validate_overflow_capacity(
        self,
        *,
        real_capacity: int,
        n_holders: int,
        per_holder_capacity: int,
    ) -> None:
        if (
            self.on_overflow == 'override_oldest'
            and real_capacity != n_holders * per_holder_capacity
        ):
            raise ValueError(
                f'IntStack: on_overflow="override_oldest" requires real '
                f'capacity ({real_capacity}) to equal n_holders * '
                f'per_holder_capacity ({n_holders} * {per_holder_capacity} '
                f'= {n_holders * per_holder_capacity}). Either drop '
                f'capacity_is_exact or pick a capacity that is a '
                f'multiple of {per_holder_capacity}.'
            )

    def add(self, value: MaybeSequence[Checkable | int]) -> None:
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

    def remove(
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
    def add(self, value: MaybeSequence[Checkable | int]) -> None:
        values = self._normalize_values(value, label='add')

        if self.on_overflow == 'override_oldest':
            with chunked(IfAll(self.counter == self.real_capacity)):
                self._cascade_right(None)
                self.counter.value -= 1
        elif self.on_overflow == 'override_newest':
            with IfAll(self.counter == self.real_capacity):
                self._overwrite_back(values)

        self._insert_at_back(values)

    def remove(
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

    def _insert_at_back(self, values: list[Checkable | int]) -> None:
        cap = self.per_holder_capacity
        bits = self.bits
        n = len(self.holders[0])

        for h in range(n - 1, -1, -1):
            upper = min((h + 1) * cap, self.real_capacity)
            with IfAll(
                h != 0 and self.counter >= h * cap,
                self.counter < upper,
            ):
                shift_amount = (self.counter - h * cap) * bits
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


class _SlotContainerBase:
    holders: Sequence[Sequence[Stat]]
    counter: Stat
    capacity: int
    width: int
    on_overflow: OnOverflow
    if_empty: IfEmptyAny
    if_present: IfPresent

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
        width = assert_same_widths(groups)

        seen: list[Stat] = []
        for group in groups:
            for stat in group:
                for prior in seen:
                    if stat.is_same_stat(prior):
                        raise ValueError(
                            f'{type(self).__name__}: holder stat {stat!r} '
                            f'is duplicated. Each slot needs its own Stat.'
                        )
                seen.append(stat)

        self.holders = groups
        self.counter = counter
        self.capacity = len(groups)
        self.width = width
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
                f'expected {self.width} (one per width-position)'
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
                f'expected {self.width} (one per width-position)'
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


class Stack(_SlotContainerBase):
    def add(self, value: MaybeSequence[Checkable | HousingType]) -> None:
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

    def remove(
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
    def add(self, value: MaybeSequence[Checkable | HousingType]) -> None:
        values = self._normalize_values(value, label='add')

        if self.on_overflow == 'override_oldest':
            with chunked(IfAll(self.counter == self.capacity)):
                self._shift_down(None)
                self.counter.value -= 1
        elif self.on_overflow == 'override_newest':
            with IfAll(self.counter == self.capacity):
                self._write_at_slot(self.capacity - 1, values)

        for i in range(self.capacity - 1, -1, -1):
            with IfAll(self.counter == i):
                self._write_at_slot(i, values)
                self.counter.value += 1

    def remove(
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
