from enum import Enum

from helpers import expect_exception

from pyhtsw import (
    Container,
    EmulatedHouse,
    GlobalStat,
    IfAll,
    PlayerStat,
    chat,
    function,
)
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
from pyhtsw.ext import Announcer, Num, Text


class Reason(Enum):
    JOIN = 0
    LEAVE = 1


def flatten(expressions: list[object]) -> list[object]:
    out: list[object] = []
    for expression in expressions:
        out.append(expression)
        if isinstance(expression, ConditionalExpression):
            out.extend(flatten(list(expression.if_expressions)))
            out.extend(flatten(list(expression.else_expressions)))
    return out


def conditionals(expressions: list[object]) -> int:
    return sum(1 for e in flatten(expressions) if isinstance(e, ConditionalExpression))


# === The enqueue is conditional-free, so it may sit inside an IfAll ===

with Container() as container:
    announcer = Announcer('Ann', capacity=6, prefix='qa')

    @announcer.format
    def joined(reason: Reason, name: Text) -> None:
        chat(f'{name} {reason.name}')

    @announcer.format
    def streak(name: Text, amount: Num, iota: Num) -> None:
        chat(f'{name} {amount} {iota}')

    gate = PlayerStat('gate').as_long()
    who = PlayerStat('who').as_string()

    @function('Caller')
    def caller() -> None:
        with IfAll(gate > 0):
            joined.announce(reason=Reason.JOIN, name=who)

    @function('Pump', repeat_ticks=5)
    def pump() -> None:
        announcer.tick()


caller_block = next(b for b in container.blocks if b.get_name() == 'Caller')
inner = flatten(list(caller_block.expressions))
# One conditional: the caller's own gate. The enqueue adds none.
assert conditionals(list(caller_block.expressions)) == 1, inner
# Two text columns are never needed here, so the row is one string plus one
# packed long: 5 shifts x 2 + 1 text write + 1 pack + 1 counter.
assert announcer.text_slots == 1
assert announcer.enqueue_actions == 5 * 2 + 1 + 5 + 1

pump_block = next(b for b in container.blocks if b.get_name() == 'Pump')
# Catch-up poll, overflow clamp, drain.
assert conditionals(list(pump_block.expressions)) == 3


# === Formats and specializations get distinct ids ===

ids = {
    specialization.title(): specialization.id
    for specialization in announcer._specializations
}
assert ids == {'Joined JOIN': 1, 'Joined LEAVE': 2, 'Streak': 3}, ids


# === Packing round-trips through the queue ===


def drain_once(ann: Announcer) -> None:
    """The drain, without the cooldown gate or the trigger."""
    ann._index.value = ann._counter
    ann._index.value -= 1
    from pyhtsw.ext.array_read_write import array_read

    array_read(
        items=ann._rows,
        index=ann._index,
        output=[*ann._current_text, ann._current_packed],
    )
    ann._counter.value -= 1


with EmulatedHouse(ignore_action_limits=True) as house:
    ann = Announcer('Ann2', capacity=4, prefix='qb')

    seen: list[tuple[int, int]] = []

    @ann.format(ranges={'amount': (0, 4000), 'iota': (-50, 50)})
    def numbers(amount: Num, iota: Num) -> None:
        chat(f'{amount}/{iota}')

    @ann.format
    def plain(name: Text) -> None:
        chat(f'{name}')

    name_stat = PlayerStat('nm').as_string()
    house.put(name_stat, 'Notch', ignore_warning=True)

    # Three rows in, FIFO out.
    numbers.announce(amount=1, iota=-50)
    numbers.announce(amount=4000, iota=50)
    plain.announce(name=name_stat)

    out_amount = GlobalStat('oam').as_long().with_auto_unset(False)
    out_iota = GlobalStat('oio').as_long().with_auto_unset(False)

    def check_first() -> None:
        assert int(house.get_raw(ann._counter)) == 3

    house.assert_all(check_first)

    for expected in ((1, -50), (4000, 50)):
        drain_once(ann)
        field_amount, field_iota = ann._formats[0].num_fields
        unpacked_amount = ann._unpack(field_amount)
        unpacked_iota = ann._unpack(field_iota)
        out_amount.value = unpacked_amount
        out_iota.value = unpacked_iota

        def check(_expected: tuple[int, int] = expected) -> None:
            assert (
                int(house.get_raw(out_amount)),
                int(house.get_raw(out_iota)),
            ) == _expected, (
                house.get_raw(out_amount),
                house.get_raw(out_iota),
                _expected,
            )

        house.assert_all(check)

    # The oldest row is the string one, and its id names the second format.
    drain_once(ann)

    def check_string() -> None:
        assert str(house.get_raw(ann._current_text[0])) == 'Notch'
        packed = int(house.get_raw(ann._current_packed))
        assert (
            packed & ((1 << ann._id_bits) - 1) == ann._formats[1].specializations[0].id
        ), packed

    house.assert_all(check_string)


# === Overflow drops the oldest and the counter is clamped ===

with EmulatedHouse(ignore_action_limits=True) as house:
    ann = Announcer('Ann3', capacity=2, prefix='qc')

    @ann.format
    def tick_message(value: Num) -> None:
        chat(f'{value}')

    for value in (10, 20, 30):
        tick_message.announce(value=value)

    out = GlobalStat('ovl').as_long().with_auto_unset(False)
    field = ann._formats[0].num_fields[0]

    ann._counter.value = 2  # what the pump's clamp would leave behind
    drain_once(ann)
    out.value = ann._unpack(field)

    def check_dropped() -> None:
        # 10 fell off the end; 20 is now the oldest.
        assert int(house.get_raw(out)) == 20, house.get_raw(out)

    house.assert_all(check_dropped)


# === A misused call site fails at build time ===

with Container():
    ann = Announcer('Ann4', prefix='qd')

    @ann.format
    def two_fields(name: Text, amount: Num) -> None:
        chat(f'{name} {amount}')

    with expect_exception(TypeError):
        two_fields.announce(name='x')  # type: ignore[call-arg]

    with expect_exception(TypeError):
        two_fields.announce(name='x', amount=1, extra=2)  # type: ignore[call-arg]

    @ann.format(ranges={'amount': (0, 10)})
    def bounded(amount: Num) -> None:
        chat(f'{amount}')

    with expect_exception(ValueError):
        bounded.announce(amount=11)


# === An unannotated or unenumerable parameter is rejected ===

with Container():
    ann = Announcer('Ann5', prefix='qe')

    with expect_exception(TypeError):

        @ann.format
        def bad(value) -> None:  # type: ignore[no-untyped-def] # noqa: ARG001
            chat('x')

    with expect_exception(TypeError):

        @ann.format
        def worse(text: str) -> None:  # noqa: ARG001
            chat('x')


# === A body may nest, and stays inside the one dispatcher ===

with Container() as container:
    ann = Announcer('Ann6', prefix='qf')

    @ann.format(ranges={'amount': (0, 100)})
    def complicated(amount: Num) -> None:
        with IfAll(amount > 5):
            chat('big')
            with IfAll(amount > 50):
                chat('huge')
        chat('done')

    @function('Pump6', repeat_ticks=5)
    def pump6() -> None:
        ann.tick()


names = {block.get_name() for block in container.blocks}
assert 'Ann6' in names and not any(n.startswith('Ann6:') for n in names), names

dispatch_block = next(b for b in container.blocks if b.get_name() == 'Ann6')
flat = flatten(list(dispatch_block.expressions))
assert not any(
    isinstance(e, ConditionalExpression)
    for parent in flat
    if isinstance(parent, ConditionalExpression)
    for e in (*parent.if_expressions, *parent.else_expressions)
), 'the dispatcher must not contain a nested conditional'
# seen guard, then the format's `chat('done')` run plus its two nested runs.
assert conditionals(list(dispatch_block.expressions)) == 4

print('test_announce OK')
