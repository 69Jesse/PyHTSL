import inspect
from collections.abc import Callable, Iterable, Mapping, Sequence
from enum import Enum
from itertools import product
from types import UnionType
from typing import TYPE_CHECKING, Literal, get_args, get_origin, overload

from pyhtsw.actions.flow import IfAll, exit_function, trigger_function
from pyhtsw.checkable import Checkable
from pyhtsw.declarations.function import Function, function
from pyhtsw.directives.preserved import Preserved
from pyhtsw.directives.strict_order import StrictOrder
from pyhtsw.editable import HousingType
from pyhtsw.expression.housing_type import NumericHousingType
from pyhtsw.ext.array_read_write import array_read
from pyhtsw.ext.nesting import Nestable
from pyhtsw.placeholders.date import DateUnixMS
from pyhtsw.stats.global_stat import GlobalStat
from pyhtsw.stats.player_stat import PlayerStat
from pyhtsw.stats.temporary_stat import TemporaryStat

if TYPE_CHECKING:
    from pyhtsw.declarations.item import Item

__all__ = (
    'Announcer',
    'Num',
    'Text',
)


type Text = Checkable
type Num = Checkable

_PAYLOAD_BITS = 62

_TEXT_FALLBACK = '-'


def _annotation_values(name: str, annotation: object) -> tuple[object, ...]:
    """The compile-time values a non-field parameter ranges over."""
    if annotation is bool:
        return (False, True)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return tuple(annotation)
    if get_origin(annotation) is Literal:
        return get_args(annotation)
    if isinstance(annotation, UnionType) or get_origin(annotation) is not None:
        raise TypeError(
            f'announcement parameter {name!r}: cannot enumerate {annotation!r}. '
            f'Annotate it Text or Num, or pass values={{{name!r}: [...]}}.',
        )
    raise TypeError(
        f'announcement parameter {name!r}: {annotation!r} is neither Text nor '
        f'Num and has no enumerable values. Annotate it Text or Num, or pass '
        f'values={{{name!r}: [...]}}.',
    )


class _TextField:
    def __init__(self, name: str, slot: int) -> None:
        self.name = name
        self.slot = slot


class _NumField:
    def __init__(self, name: str, span: tuple[int, int] | None) -> None:
        self.name = name
        self.span = span
        self.bits = 0
        self.bias = 0
        self.shift = 0
        self.top = False

    @property
    def low(self) -> int:
        return self.span[0] if self.span is not None else -self.bias

    @property
    def high(self) -> int:
        if self.span is not None:
            return self.span[1]
        return (1 << self.bits) - 1 - self.bias


type _UnpackKey = tuple[int, int, int | None]


def _unpack_key(field: '_NumField') -> _UnpackKey:
    # A top field emits no mask, so its width does not change the code.
    return (field.shift, field.bias, None if field.top else field.bits)


class _ConstField:
    def __init__(self, name: str, values: tuple[object, ...]) -> None:
        self.name = name
        self.values = values


class _Specialization:
    def __init__(
        self,
        owner: '_FormatBase',
        consts: tuple[object, ...],
    ) -> None:
        self.owner = owner
        self.consts = consts
        self.id = 0

    @property
    def const_arguments(self) -> dict[str, object]:
        return {
            field.name: value
            for field, value in zip(self.owner.const_fields, self.consts, strict=True)
        }

    def title(self) -> str:
        parts = [self.owner.title]
        for field, value in zip(self.owner.const_fields, self.consts, strict=True):
            parts.append(_readable(value, field.values.index(value)))
        return ' '.join(parts)


def _readable(value: object, index: int = 0) -> str:
    name = getattr(value, 'name', None)
    if isinstance(name, str):
        return name
    if isinstance(value, bool | int | str):
        return str(value)
    return str(index)


def _title_from_callback(callback: Callable[..., None]) -> str:
    return callback.__name__.replace('_', ' ').title()


class _FormatBase:
    def __init__(
        self,
        announcer: 'Announcer',
        callback: Callable[..., None],
        *,
        title: str,
        values: Mapping[str, Iterable[object]] | None,
        ranges: Mapping[str, tuple[int, int]] | None,
    ) -> None:
        self.announcer = announcer
        self.callback = callback
        self.title = title
        self.signature = inspect.signature(callback)

        annotations = inspect.get_annotations(callback, eval_str=True)
        ranges = dict(ranges or {})
        values = {name: tuple(vs) for name, vs in (values or {}).items()}

        self.text_fields: list[_TextField] = []
        self.num_fields: list[_NumField] = []
        self.const_fields: list[_ConstField] = []
        self.order: list[str] = []

        for name in self.signature.parameters:
            self.order.append(name)
            if name in values:
                self.const_fields.append(_ConstField(name, values[name]))
                continue
            if name not in annotations:
                raise TypeError(
                    f'announcement parameter {name!r} of {title!r} has no '
                    f'annotation; annotate it Text or Num.',
                )
            annotation = annotations[name]
            if annotation is Text:
                self.text_fields.append(_TextField(name, len(self.text_fields)))
            elif annotation is Num:
                self.num_fields.append(_NumField(name, ranges.pop(name, None)))
            else:
                self.const_fields.append(
                    _ConstField(name, _annotation_values(name, annotation)),
                )

        if ranges:
            raise TypeError(
                f'{title!r}: ranges names {sorted(ranges)} which are not Num '
                f'parameters',
            )

        self.specializations = [
            _Specialization(self, consts)
            for consts in product(*(field.values for field in self.const_fields))
        ]
        if not self.specializations:
            raise ValueError(f'{title!r}: a const parameter has no values')

    def assign_bits(self, id_bits: int) -> None:
        available = _PAYLOAD_BITS - id_bits
        declared = [f for f in self.num_fields if f.span is not None]
        undeclared = [f for f in self.num_fields if f.span is None]
        for field in declared:
            low, high = field.span  # type: ignore[misc]
            if high < low:
                raise ValueError(
                    f'{self.title!r}: range for {field.name!r} is empty',
                )
            field.bits = max(1, (high - low).bit_length())
            field.bias = -low
        spare = available - sum(field.bits for field in declared)
        if undeclared:
            each = spare // len(undeclared)
            if each < 1:
                raise ValueError(
                    f'{self.title!r}: no bits left for {len(undeclared)} '
                    f'undeclared Num field(s); give them explicit ranges',
                )
            for field in undeclared:
                field.bits = each
                field.bias = 1 << (each - 1)
        total = sum(field.bits for field in self.num_fields)
        if total > available:
            raise ValueError(
                f'{self.title!r}: Num fields need {total} bits but only '
                f'{available} are available',
            )
        shift = id_bits
        for field in self.num_fields:
            field.shift = shift
            shift += field.bits
        if self.num_fields:
            self.num_fields[-1].top = True

    def bind(
        self,
        args: Sequence[object],
        kwargs: Mapping[str, object],
    ) -> dict[str, object]:
        bound = self.signature.bind(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)

    def specialization_for(self, bound: Mapping[str, object]) -> _Specialization:
        consts = tuple(bound[field.name] for field in self.const_fields)
        for specialization in self.specializations:
            if specialization.consts == consts:
                return specialization
        listed = ', '.join(
            f'{field.name}={value!r}'
            for field, value in zip(self.const_fields, consts, strict=True)
        )
        raise ValueError(
            f'{self.title!r}: no declared specialization for {listed}. Pass '
            f'values={{...}} to widen the set.',
        )


class Format[**P]:
    """One declared announcement, returned by ``Announcer.format``.

    Calling ``announce`` emits the inline enqueue: a shift, a row write and a
    counter bump, with no conditionals, so it may sit inside an ``IfAll``.
    """

    def __init__(self, base: _FormatBase) -> None:
        self._base = base

    @property
    def title(self) -> str:
        return self._base.title

    def announce(self, *args: P.args, **kwargs: P.kwargs) -> None:
        base = self._base
        bound = base.bind(args, kwargs)
        base.announcer._emit_announce(base.specialization_for(bound), bound)


class Announcer:
    """A house-wide announcement queue.

    Housing runs a function at most once every four ticks per player, so two
    global messages fired from one tick lose the second one. Every message
    declared here shares a single dispatch function and a queue of pending
    rows: the enqueue is inline and conditional-free, and one pending row is
    released per ``cooldown_ms``, which keeps that dispatch off its cooldown.

    Rows carry the arguments, not the text: a Housing string holds 32
    characters, so a rendered message can never be stored. Each row is
    ``text_slots`` shared string columns plus one long that packs the format
    id and every ``Num`` field.
    """

    def __init__(
        self,
        name: str = 'Global Announcement',
        *,
        capacity: int = 8,
        cooldown_ms: int = 400,
        prefix: str = 'ga',
        icon: 'Item | None' = None,
    ) -> None:
        if capacity < 1:
            raise ValueError('Announcer: capacity must be at least 1')
        if cooldown_ms < 250:
            raise ValueError(
                'Announcer: cooldown_ms below 250 cannot clear the four-tick '
                'function cooldown on a lagging server',
            )
        self.name = name
        self.capacity = capacity
        self.cooldown_ms = cooldown_ms
        self.prefix = prefix
        self.icon = icon

        self._formats: list[_FormatBase] = []
        self._specializations: list[_Specialization] = []
        self._dispatch: Function | None = None
        self._rows: list[tuple[GlobalStat, ...]] | None = None
        self._id_bits = 0

    @overload
    def format[**P](self, callback: Callable[P, None], /) -> Format[P]: ...

    @overload
    def format[**P](
        self,
        /,
        *,
        name: str | None = ...,
        values: Mapping[str, Iterable[object]] | None = ...,
        ranges: Mapping[str, tuple[int, int]] | None = ...,
    ) -> Callable[[Callable[P, None]], Format[P]]: ...

    def format[**P](
        self,
        callback: Callable[P, None] | None = None,
        /,
        *,
        name: str | None = None,
        values: Mapping[str, Iterable[object]] | None = None,
        ranges: Mapping[str, tuple[int, int]] | None = None,
    ) -> Format[P] | Callable[[Callable[P, None]], Format[P]]:
        """Declare a message.

        A parameter annotated ``Text`` takes one of the shared string columns,
        one annotated ``Num`` takes a bit range in the shared packed long, and
        any other parameter is compile time: the announcer emits one format id
        per value, so a discriminator costs a dispatcher conditional rather
        than a queue column.

        A body may open conditionals to any depth; the dispatcher lowers them.
        """

        def decorator(callback: Callable[P, None]) -> Format[P]:
            if self._rows is not None:
                raise RuntimeError(
                    f'{self.name}: cannot declare {callback.__name__!r} after '
                    f'the layout is fixed; declare every format at import time',
                )
            base = _FormatBase(
                self,
                callback,
                title=name or _title_from_callback(callback),
                values=values,
                ranges=ranges,
            )
            self._formats.append(base)
            self._specializations.extend(base.specializations)
            self._ensure_dispatch()
            return Format(base)

        if callback is not None:
            return decorator(callback)
        return decorator

    def _ensure_dispatch(self) -> None:
        if self._dispatch is not None:
            return

        @function(self.name, icon=self.icon)
        def dispatch() -> None:
            self._emit_dispatch()

        self._dispatch = dispatch

    @property
    def text_slots(self) -> int:
        return max(
            (len(base.text_fields) for base in self._formats),
            default=0,
        )

    def _ensure_layout(self) -> None:
        if self._rows is not None:
            return
        if not self._formats:
            raise RuntimeError(f'{self.name}: no formats declared')

        # Id 0 stays free so an unset packed column never names a format.
        for index, specialization in enumerate(self._specializations, start=1):
            specialization.id = index
        self._id_bits = max(1, len(self._specializations).bit_length())
        for base in self._formats:
            base.assign_bits(self._id_bits)

        prefix = self.prefix
        slots = self.text_slots
        self._rows = [
            (
                *(
                    GlobalStat(f'{prefix}{slot}_{row}')
                    .as_string()
                    .with_auto_unset(False)
                    .with_fallback(_TEXT_FALLBACK)
                    for slot in range(slots)
                ),
                GlobalStat(f'{prefix}p_{row}').as_long().with_auto_unset(False),
            )
            for row in range(self.capacity)
        ]
        self._current_text = [
            GlobalStat(f'{prefix}c{slot}')
            .as_string()
            .with_auto_unset(False)
            .with_fallback(_TEXT_FALLBACK)
            for slot in range(slots)
        ]
        self._current_packed = (
            GlobalStat(f'{prefix}cp').as_long().with_auto_unset(False)
        )
        self._counter = GlobalStat(f'{prefix}n').as_long().with_auto_unset(False)
        self._next_at = GlobalStat(f'{prefix}t').as_long().with_auto_unset(False)
        self._sequence = GlobalStat(f'{prefix}q').as_long().with_auto_unset(False)
        self._seen = PlayerStat(f'{prefix}s').as_long().with_auto_unset(False)
        # A plain PlayerStat index takes array_read's direct composed-name
        # path, which a TemporaryStat would miss. The name is the bare prefix
        # because that path only has 32 characters to spend on the whole
        # composed reference, and the text columns' fallback eats two of them.
        self._index = PlayerStat(prefix).as_long().with_auto_unset(False)

    @property
    def enqueue_actions(self) -> int:
        """Worst-case CHANGE_VARs one ``announce`` emits, over every format."""
        self._ensure_layout()
        assert self._rows is not None
        width = len(self._rows[0])
        shift = (self.capacity - 1) * width
        worst = 0
        for base in self._formats:
            pack = 1 if not base.num_fields else 2 * len(base.num_fields) + 1
            worst = max(worst, len(base.text_fields) + pack)
        return shift + worst + 1

    def _emit_announce(
        self,
        specialization: _Specialization,
        bound: Mapping[str, object],
    ) -> None:
        self._ensure_layout()
        assert self._rows is not None
        base = specialization.owner
        rows = self._rows
        width = len(rows[0])

        # The rows are only ever read back through a composed placeholder name,
        # so nothing static can see that these writes are live, and the shift
        # order is the structure itself.
        with StrictOrder(), Preserved():
            for row in range(self.capacity - 1, 0, -1):
                for column in range(width):
                    rows[row][column].value = rows[row - 1][column]
            # An unused text column keeps whatever the shift left there; the
            # format that reads a column is the one that wrote it.
            for text_field in base.text_fields:
                rows[0][text_field.slot].value = _as_value(bound[text_field.name])
            self._emit_pack(rows[0][-1], specialization, bound)
            self._counter.value += 1

    def _emit_pack(
        self,
        destination: GlobalStat,
        specialization: _Specialization,
        bound: Mapping[str, object],
    ) -> None:
        fields = specialization.owner.num_fields
        # Every bias sits at a fixed bit position, and so does any field the
        # call site passed as a literal, so all of them fold into the one
        # constant the id already needs. `Preserved` keeps the optimizer's
        # folder away from these writes, which is why it happens here.
        constant = specialization.id
        dynamic: list[_NumField] = []
        for field in fields:
            constant += field.bias << field.shift
            value = bound[field.name]
            if isinstance(value, bool) or not isinstance(value, int):
                dynamic.append(field)
                continue
            if not (field.low <= value <= field.high):
                raise ValueError(
                    f'{specialization.owner.title!r}: {field.name}={value} is '
                    f'outside the {field.bits}-bit range '
                    f'[{field.low}, {field.high}]; pass ranges={{...}}',
                )
            constant += value << field.shift

        if not dynamic:
            destination.value = constant
            return
        # Horner from the top field down, straight into the slot, so packing
        # costs two actions per field and needs no scratch.
        destination.value = _as_number(bound[dynamic[-1].name])
        previous = dynamic[-1].shift
        for field in reversed(dynamic[:-1]):
            destination.value *= 1 << (previous - field.shift)
            destination.value += _as_number(bound[field.name])
            previous = field.shift
        if previous:
            destination.value *= 1 << previous
        if constant:
            destination.value += constant

    def _emit_dispatch(self) -> None:
        self._ensure_layout()
        with Nestable():
            with IfAll(self._seen == self._sequence):
                exit_function()
            self._seen.value = self._sequence

            identifier = TemporaryStat().as_long()
            identifier.value = self._current_packed
            identifier.value &= (1 << self._id_bits) - 1

            # Unguarded, and shared by every format with the same layout: a
            # guarded unpack costs a whole conditional per format, and the
            # result is only ever read under that format's own branch.
            unpacked: dict[_UnpackKey, TemporaryStat] = {}
            for base in self._formats:
                for num_field in base.num_fields:
                    key = _unpack_key(num_field)
                    if key not in unpacked:
                        unpacked[key] = self._unpack(num_field)

            for specialization in self._specializations:
                with IfAll(identifier == specialization.id):
                    self._emit_body(specialization, unpacked)

    def _emit_body(
        self,
        specialization: _Specialization,
        unpacked: dict[_UnpackKey, TemporaryStat],
    ) -> None:
        base = specialization.owner
        arguments: dict[str, object] = specialization.const_arguments
        for text_field in base.text_fields:
            arguments[text_field.name] = self._current_text[text_field.slot]
        for num_field in base.num_fields:
            arguments[num_field.name] = unpacked[_unpack_key(num_field)]
        base.callback(**{name: arguments[name] for name in base.order})

    def _unpack(self, field: _NumField) -> TemporaryStat:
        value = TemporaryStat().as_long()
        value.value = self._current_packed
        if field.shift:
            value.value >>= field.shift
        if not field.top:
            value.value &= (1 << field.bits) - 1
        if field.bias:
            value.value -= field.bias
        return value

    def tick(self) -> None:
        """Release pending announcements. Put this in a per-player loop.

        Emits the catch-up poll first, so the player who releases a row is
        served by the same all-players trigger everyone else gets.
        """
        if not self._formats:
            return
        self._ensure_layout()
        assert self._rows is not None
        assert self._dispatch is not None

        with IfAll(self._seen != self._sequence):
            trigger_function(self._dispatch)

        # Only reachable if a row was dropped on overflow; the shift already
        # discarded it, this is the bookkeeping.
        with IfAll(self._counter > self.capacity):
            self._counter.value = self.capacity

        with IfAll(self._counter > 0, self._next_at <= DateUnixMS):
            self._next_at.value = DateUnixMS + self.cooldown_ms
            self._index.value = self._counter
            self._index.value -= 1
            array_read(
                items=self._rows,
                index=self._index,
                output=[*self._current_text, self._current_packed],
            )
            self._counter.value -= 1
            self._sequence.value += 1
            trigger_function(self._dispatch, trigger_for_all_players=True)

    def on_join(self) -> None:
        """Mark a joining player as having seen the current announcement.

        Without it a fresh player, whose seen counter starts at zero, renders
        whatever was last released.
        """
        if not self._formats:
            return
        self._ensure_layout()
        self._seen.value = self._sequence


def _as_value(value: object) -> Checkable | HousingType:
    if isinstance(value, Checkable | int | float | str | bool):
        return value  # type: ignore[return-value]
    raise TypeError(
        f'announcement argument {value!r} is neither a Checkable nor a plain '
        f'long/double/string value',
    )


def _as_number(value: object) -> Checkable | NumericHousingType:
    if isinstance(value, Checkable | int | float | bool):
        return value  # type: ignore[return-value]
    raise TypeError(
        f'announcement Num argument {value!r} is neither a Checkable nor a '
        f'plain number',
    )
