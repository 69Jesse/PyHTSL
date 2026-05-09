"""Tests for the stack/queue implementations in `pyhtsl.ext.stack_queue`.

Covers `IntStack` today; future stack/queue types in the same module should add
their cases here rather than spawning a parallel file.

Capacity arithmetic used throughout:
    most=255  -> bit_length=8  -> per_holder_capacity = 63 // 8 = 7
    most=1023 -> bit_length=10 -> per_holder_capacity = 63 // 10 = 6
"""

from helpers import expect_exception

from pyhtsl import ExecutionContext, PlayerStat
from pyhtsl.ext.stack_queue import IntQueue, IntStack, Queue, Stack

# === Single holder, width 1 ===

# Push then pop returns the most recent value.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    s = IntStack(holder=h, counter=counter, most=255)
    s.add(42)
    s.add(7)
    s.remove(output=out)

    def check_top() -> None:
        assert int(ctx.get(out)) == 7

    ctx.assert_all(check_top)


# Push N values, pop them all in LIFO order.
for _n in (1, 5, 7):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        h = PlayerStat('h').as_long()
        counter = PlayerStat('c').as_long()
        outs = [PlayerStat(f'o{i}').as_long() for i in range(_n)]
        s = IntStack(holder=h, counter=counter, most=255)
        for i in range(_n):
            s.add((i + 1) * 11)
        for i in range(_n):
            s.remove(output=outs[i])

        def check_lifo(_count: int = _n, _outs: list = outs) -> None:
            for i in range(_count):
                got = int(ctx.get(_outs[i]))
                want = (_count - i) * 11
                assert got == want, f'pop {i}: got {got}, want {want}'

        ctx.assert_all(check_lifo)


# Pop on an empty stack writes -1 to the output.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    s = IntStack(holder=h, counter=counter, most=255)
    s.remove(output=out)

    def check_empty() -> None:
        assert int(ctx.get(out)) == -1

    ctx.assert_all(check_empty)


# Custom `if_empty` sentinel: empty pop writes the configured value, and
# a successful pop is unaffected (still returns the actual value).
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out_empty = PlayerStat('oe').as_long()
    out_real = PlayerStat('or').as_long()
    s = IntStack(holder=h, counter=counter, most=255, if_empty=999)
    s.remove(output=out_empty)
    s.add(42)
    s.remove(output=out_real)

    def check_custom_sentinel() -> None:
        assert int(ctx.get(out_empty)) == 999
        assert int(ctx.get(out_real)) == 42

    ctx.assert_all(check_custom_sentinel)


# `if_empty` can also be a Checkable (read from another stat at HTSL time).
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    sentinel_src = PlayerStat('sentinel').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(sentinel_src, 7777, ignore_warning=True)
    s = IntStack(holder=h, counter=counter, most=255, if_empty=sentinel_src)
    s.remove(output=out)

    def check_dynamic_sentinel() -> None:
        assert int(ctx.get(out)) == 7777

    ctx.assert_all(check_dynamic_sentinel)


# `if_empty` as a Callable runs inside the Else context instead of writing
# to outputs. Lets the caller emit arbitrary HTSL on empty.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    flag = PlayerStat('flag').as_long()
    ctx.put(out, 123, ignore_warning=True)  # so we can detect "untouched"

    def on_empty() -> None:
        flag.value = 1

    s = IntStack(holder=h, counter=counter, most=255, if_empty=on_empty)
    s.remove(output=out)

    def check_callable_empty() -> None:
        assert int(ctx.get(flag)) == 1
        assert int(ctx.get(out)) == 123  # output untouched

    ctx.assert_all(check_callable_empty)


# `if_empty=None` skips the Else entirely — output is left at whatever it
# previously held.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(out, 555, ignore_warning=True)
    s = IntStack(holder=h, counter=counter, most=255, if_empty=None)
    s.remove(output=out)

    def check_none_empty() -> None:
        assert int(ctx.get(out)) == 555

    ctx.assert_all(check_none_empty)


# `if_present` runs inside the IF body whenever the pop succeeds.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    pops = PlayerStat('pops').as_long()

    def on_pop() -> None:
        pops.value += 1

    s = IntStack(holder=h, counter=counter, most=255, if_present=on_pop)
    s.add(10)
    s.add(20)
    s.remove(output=out)  # success -> pops=1
    s.remove(output=out)  # success -> pops=2
    s.remove(output=out)  # empty   -> pops stays at 2

    def check_if_present() -> None:
        assert int(ctx.get(pops)) == 2

    ctx.assert_all(check_if_present)


# Per-call `if_empty` / `if_present` override the class-level values. The
# per-call argument takes precedence — including the ability to suppress
# a class-level callback by passing None.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out_class = PlayerStat('oc').as_long()
    out_override = PlayerStat('oo').as_long()
    out_suppress = PlayerStat('os').as_long()
    ctx.put(out_suppress, 42, ignore_warning=True)
    s = IntStack(holder=h, counter=counter, most=255, if_empty=100)
    s.remove(output=out_class)  # uses class-level 100
    s.remove(output=out_override, if_empty=200)  # overrides to 200
    s.remove(output=out_suppress, if_empty=None)  # suppresses, untouched

    def check_per_call() -> None:
        assert int(ctx.get(out_class)) == 100
        assert int(ctx.get(out_override)) == 200
        assert int(ctx.get(out_suppress)) == 42

    ctx.assert_all(check_per_call)


# Counter tracks current depth.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    s = IntStack(holder=h, counter=counter, most=255)
    s.add(1)
    s.add(2)
    s.add(3)

    def check_counter() -> None:
        assert int(ctx.get(counter)) == 3

    ctx.assert_all(check_counter)


# Push, pop to empty, then pop again -> -1 (counter doesn't go negative).
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out_first = PlayerStat('of').as_long()
    out_second = PlayerStat('os').as_long()
    s = IntStack(holder=h, counter=counter, most=255)
    s.add(99)
    s.remove(output=out_first)
    s.remove(output=out_second)

    def check_double_pop() -> None:
        assert int(ctx.get(out_first)) == 99
        assert int(ctx.get(out_second)) == -1
        assert int(ctx.get(counter)) == 0

    ctx.assert_all(check_double_pop)


# === Overflow modes (single holder, capacity == per_holder_capacity) ===

# 'ignore': pushes past capacity are no-ops; the original 7 values survive.
# (capacity_is_exact pins real_capacity to 7 even though per_holder_capacity
# would otherwise grow to 8 for bits=8.)
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(7)]
    s = IntStack(
        holder=h,
        counter=counter,
        most=255,
        capacity=7,
        capacity_is_exact=True,
        on_overflow='ignore',
    )
    for i in range(10):  # 7 successful pushes, 3 ignored
        s.add(i + 1)

    def check_counter_saturated() -> None:
        assert int(ctx.get(counter)) == 7

    ctx.assert_all(check_counter_saturated)
    for i in range(7):
        s.remove(output=outs[i])

    def check_ignore_pops(_outs: list = outs) -> None:
        for i in range(7):
            got = int(ctx.get(_outs[i]))
            want = 7 - i
            assert got == want, f'ignore pop {i}: got {got}, want {want}'

    ctx.assert_all(check_ignore_pops)


# 'override_newest': pushes past capacity replace the top in place.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(7)]
    s = IntStack(
        holder=h,
        counter=counter,
        most=255,
        capacity=7,
        capacity_is_exact=True,
        on_overflow='override_newest',
    )
    for i in range(10):  # values 1..6 stay, then 7 is replaced repeatedly by 8, 9, 10
        s.add(i + 1)

    def check_stack_override_newest_counter() -> None:
        assert int(ctx.get(counter)) == 7

    ctx.assert_all(check_stack_override_newest_counter)
    for i in range(7):
        s.remove(output=outs[i])

    def check_stack_override_newest(_outs: list = outs) -> None:
        # Stored: [1, 2, 3, 4, 5, 6, 10] (top = 10, since 7,8,9 each got
        # replaced by the next push). LIFO pop order: 10, 6, 5, 4, 3, 2, 1.
        expected = [10, 6, 5, 4, 3, 2, 1]
        for i, want in enumerate(expected):
            got = int(ctx.get(_outs[i]))
            assert got == want, f'stack override_newest pop {i}: got {got}, want {want}'

    ctx.assert_all(check_stack_override_newest)


# 'override_oldest': pushes past capacity drop the oldest; counter stays full.
# (Stack's override_oldest requires real_capacity == n_holders * per_holder
# _capacity, so we use the natural single-holder capacity for bits=8: 8.)
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(8)]
    s = IntStack(
        holder=h,
        counter=counter,
        most=255,
        capacity=8,
        on_overflow='override_oldest',
    )
    for i in range(11):  # values 1..3 get dropped, 4..11 survive
        s.add(i + 1)

    def check_override_counter() -> None:
        assert int(ctx.get(counter)) == 8

    ctx.assert_all(check_override_counter)
    for i in range(8):
        s.remove(output=outs[i])

    def check_override_pops(_outs: list = outs) -> None:
        for i in range(8):
            got = int(ctx.get(_outs[i]))
            want = 11 - i  # LIFO of [4..11]
            assert got == want, f'override pop {i}: got {got}, want {want}'

    ctx.assert_all(check_override_pops)


# === Multi-holder cascade ===
# most=255 -> per_holder_capacity=8; capacity=14 -> n_holders=2, real_cap=16
# (default growth fills both holders).

# Push past per_holder_capacity to force the carry between holders.
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(14)]
    s = IntStack(
        holder=lambda i: PlayerStat(f'mh{i}').as_long(),
        counter=counter,
        most=255,
        capacity=14,
    )
    for i in range(14):
        s.add(i + 1)
    for i in range(14):
        s.remove(output=outs[i])

    def check_cascade(_outs: list = outs) -> None:
        for i in range(14):
            got = int(ctx.get(_outs[i]))
            want = 14 - i
            assert got == want, f'cascade pop {i}: got {got}, want {want}'

    ctx.assert_all(check_cascade)


# Multi-holder + override_oldest: oldest cascades out the top of the last holder.
# (capacity=14 grows to real_capacity=16 = 2*per_holder_capacity, satisfying the
# stack's override_oldest tile-evenness requirement.)
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(16)]
    s = IntStack(
        holder=lambda i: PlayerStat(f'oh{i}').as_long(),
        counter=counter,
        most=255,
        capacity=14,
        on_overflow='override_oldest',
    )
    for i in range(22):  # values 1..6 dropped, 7..22 survive
        s.add(i + 1)
    for i in range(16):
        s.remove(output=outs[i])

    def check_multi_override(_outs: list = outs) -> None:
        for i in range(16):
            got = int(ctx.get(_outs[i]))
            want = 22 - i  # LIFO of [7..22]
            assert got == want, f'multi-override pop {i}: got {got}, want {want}'

    ctx.assert_all(check_multi_override)


# Multi-holder partial fill: pushing fewer values than per_holder_capacity
# stays in holder 0 entirely; pop should still work and counter should
# drain to 0.
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(3)]
    s = IntStack(
        holder=lambda i: PlayerStat(f'ph{i}').as_long(),
        counter=counter,
        most=255,
        capacity=14,
    )
    s.add(11)
    s.add(22)
    s.add(33)
    for i in range(3):
        s.remove(output=outs[i])

    def check_partial(_outs: list = outs) -> None:
        assert int(ctx.get(_outs[0])) == 33
        assert int(ctx.get(_outs[1])) == 22
        assert int(ctx.get(_outs[2])) == 11
        assert int(ctx.get(counter)) == 0

    ctx.assert_all(check_partial)


# === Width > 1: parallel sub-stacks share one counter ===

# most=1023 keeps room for the second column's larger values (up to 300).
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [
        (PlayerStat(f'oa{i}').as_long(), PlayerStat(f'ob{i}').as_long())
        for i in range(3)
    ]
    s = IntStack(
        holder=(PlayerStat('ha').as_long(), PlayerStat('hb').as_long()),
        counter=counter,
        most=1023,
    )
    s.add((1, 100))
    s.add((2, 200))
    s.add((3, 300))
    for i in range(3):
        s.remove(output=outs[i])

    def check_width2(_outs: list = outs) -> None:
        expected = [(3, 300), (2, 200), (1, 100)]
        for i, (oa, ob) in enumerate(_outs):
            got = (int(ctx.get(oa)), int(ctx.get(ob)))
            assert got == expected[i], f'width2 pop {i}: got {got}, want {expected[i]}'

    ctx.assert_all(check_width2)


# Width > 1 + multi-holder: each width-position has its own n_holders chain.
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [
        (PlayerStat(f'wa{i}').as_long(), PlayerStat(f'wb{i}').as_long())
        for i in range(12)
    ]
    s = IntStack(
        holder=(
            lambda i: PlayerStat(f'wha{i}').as_long(),
            lambda i: PlayerStat(f'whb{i}').as_long(),
        ),
        counter=counter,
        most=1023,
        capacity=12,
    )
    for i in range(12):
        s.add((i + 1, (i + 1) * 10))
    for i in range(12):
        s.remove(output=outs[i])

    def check_width2_multi(_outs: list = outs) -> None:
        for i in range(12):
            n = 12 - i
            got = (int(ctx.get(_outs[i][0])), int(ctx.get(_outs[i][1])))
            want = (n, n * 10)
            assert got == want, f'width2-multi pop {i}: got {got}, want {want}'

    ctx.assert_all(check_width2_multi)


# === Init failure cases ===

# most < 1 -> assertion
with expect_exception(AssertionError):
    IntStack(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=0,
    )

# capacity == 0 -> ValueError
with expect_exception(ValueError):
    IntStack(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=0,
    )

# capacity negative -> ValueError
with expect_exception(ValueError):
    IntStack(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=-3,
    )

# Single Stat for stack needing multiple holders -> duplicate detection.
with expect_exception(ValueError):
    IntStack(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=14,
    )

# Empty holder list -> ValueError
with expect_exception(ValueError):
    IntStack(
        holder=[],
        counter=PlayerStat('c').as_long(),
        most=255,
    )

# Factory that returns the same stat for every i -> duplicate detection.
with expect_exception(ValueError):
    fixed = PlayerStat('fixed').as_long()
    IntStack(
        holder=lambda _i, _s=fixed: _s,
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=14,
    )

# override_oldest + exact mode where real_capacity doesn't tile evenly.
with expect_exception(ValueError):
    IntStack(
        holder=lambda i: PlayerStat(f'eh{i}').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=10,
        capacity_is_exact=True,
        on_overflow='override_oldest',
    )


# === push / pop failure cases ===

# Wrong-length push sequence on a width-1 stack.
with expect_exception(ValueError):
    s = IntStack(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    s.add((1, 2))

# Wrong-length push sequence on a width-2 stack (single value).
with expect_exception(ValueError):
    s = IntStack(
        holder=(PlayerStat('ha').as_long(), PlayerStat('hb').as_long()),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    s.add(1)

# Wrong-length pop output on a width-1 stack.
with expect_exception(ValueError):
    s = IntStack(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    s.remove(output=(PlayerStat('a').as_long(), PlayerStat('b').as_long()))

# Push value out of range (negative).
with expect_exception(ValueError):
    s = IntStack(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    s.add(-1)

# Push value out of range (above most).
with expect_exception(ValueError):
    s = IntStack(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    s.add(256)


# ===========================================================================
# IntQueue
# ===========================================================================

# === Single holder, width 1, basic FIFO ===

# Enqueue then dequeue returns the OLDEST value (not the newest).
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    q = IntQueue(holder=h, counter=counter, most=255)
    q.add(42)
    q.add(7)
    q.remove(output=out)

    def check_front() -> None:
        assert int(ctx.get(out)) == 42

    ctx.assert_all(check_front)


# Enqueue N values, dequeue them all in FIFO order.
for _n in (1, 5, 7):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        h = PlayerStat('h').as_long()
        counter = PlayerStat('c').as_long()
        outs = [PlayerStat(f'o{i}').as_long() for i in range(_n)]
        q = IntQueue(holder=h, counter=counter, most=255)
        for i in range(_n):
            q.add((i + 1) * 11)
        for i in range(_n):
            q.remove(output=outs[i])

        def check_fifo(_count: int = _n, _outs: list = outs) -> None:
            for i in range(_count):
                got = int(ctx.get(_outs[i]))
                want = (i + 1) * 11
                assert got == want, f'dequeue {i}: got {got}, want {want}'

        ctx.assert_all(check_fifo)


# Dequeue on an empty queue writes -1 to the output.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    q = IntQueue(holder=h, counter=counter, most=255)
    q.remove(output=out)

    def check_dequeue_empty() -> None:
        assert int(ctx.get(out)) == -1

    ctx.assert_all(check_dequeue_empty)


# Custom `if_empty` sentinel for IntQueue: empty dequeue writes the
# configured value; a successful dequeue is unaffected.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out_empty = PlayerStat('oe').as_long()
    out_real = PlayerStat('or').as_long()
    q = IntQueue(holder=h, counter=counter, most=255, if_empty=42)
    q.remove(output=out_empty)
    q.add(99)
    q.remove(output=out_real)

    def check_q_custom_sentinel() -> None:
        assert int(ctx.get(out_empty)) == 42
        assert int(ctx.get(out_real)) == 99

    ctx.assert_all(check_q_custom_sentinel)


# Counter tracks current depth.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    q = IntQueue(holder=h, counter=counter, most=255)
    q.add(1)
    q.add(2)
    q.add(3)

    def check_q_counter() -> None:
        assert int(ctx.get(counter)) == 3

    ctx.assert_all(check_q_counter)


# Interleaved enqueue/dequeue keeps FIFO order.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    out_a = PlayerStat('oa').as_long()
    out_b = PlayerStat('ob').as_long()
    out_c = PlayerStat('oc').as_long()
    q = IntQueue(holder=h, counter=counter, most=255)
    q.add(11)
    q.add(22)
    q.remove(output=out_a)  # 11
    q.add(33)
    q.remove(output=out_b)  # 22
    q.remove(output=out_c)  # 33

    def check_interleave() -> None:
        assert int(ctx.get(out_a)) == 11
        assert int(ctx.get(out_b)) == 22
        assert int(ctx.get(out_c)) == 33
        assert int(ctx.get(counter)) == 0

    ctx.assert_all(check_interleave)


# === Overflow modes ===

# 'ignore': enqueue past capacity is a no-op; the original 7 survive.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(7)]
    q = IntQueue(
        holder=h,
        counter=counter,
        most=255,
        capacity=7,
        capacity_is_exact=True,
        on_overflow='ignore',
    )
    for i in range(10):  # 7 successful enqueues, 3 ignored
        q.add(i + 1)
    for i in range(7):
        q.remove(output=outs[i])

    def check_q_ignore(_outs: list = outs) -> None:
        for i in range(7):
            got = int(ctx.get(_outs[i]))
            want = i + 1
            assert got == want, f'q-ignore deq {i}: got {got}, want {want}'

    ctx.assert_all(check_q_ignore)


# 'override_oldest': enqueue past capacity drops the FRONT (oldest).
# Queue's override_oldest doesn't require tile-evenness, so we can pin
# real_capacity to 7 with capacity_is_exact=True.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(7)]
    q = IntQueue(
        holder=h,
        counter=counter,
        most=255,
        capacity=7,
        capacity_is_exact=True,
        on_overflow='override_oldest',
    )
    for i in range(10):  # values 1..3 dropped, 4..10 survive
        q.add(i + 1)
    for i in range(7):
        q.remove(output=outs[i])

    def check_q_override(_outs: list = outs) -> None:
        for i in range(7):
            got = int(ctx.get(_outs[i]))
            want = i + 4  # FIFO of [4..10]
            assert got == want, f'q-override deq {i}: got {got}, want {want}'

    ctx.assert_all(check_q_override)


# 'override_newest' for queue: drop the BACK and replace with new.
with ExecutionContext(ignore_action_limits=True) as ctx:
    h = PlayerStat('h').as_long()
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(7)]
    q = IntQueue(
        holder=h,
        counter=counter,
        most=255,
        capacity=7,
        capacity_is_exact=True,
        on_overflow='override_newest',
    )
    for i in range(10):  # 1..7 fill; 8, 9, 10 each replace the back
        q.add(i + 1)

    def check_q_override_newest_counter() -> None:
        assert int(ctx.get(counter)) == 7

    ctx.assert_all(check_q_override_newest_counter)
    for i in range(7):
        q.remove(output=outs[i])

    def check_q_override_newest(_outs: list = outs) -> None:
        # Stored: [1, 2, 3, 4, 5, 6, 10] (front -> back).
        expected = [1, 2, 3, 4, 5, 6, 10]
        for i, want in enumerate(expected):
            got = int(ctx.get(_outs[i]))
            assert got == want, f'q override_newest deq {i}: got {got}, want {want}'

    ctx.assert_all(check_q_override_newest)


# Queue's override_newest works with multi-holder where the back slot lives
# in the LAST holder. (capacity=14 grows to real_capacity=16 by default.)
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(16)]
    q = IntQueue(
        holder=lambda i: PlayerStat(f'nq{i}').as_long(),
        counter=counter,
        most=255,
        capacity=14,
        on_overflow='override_newest',
    )
    for i in range(20):  # 1..16 fill; 17..20 each replace the back
        q.add(i + 1)
    for i in range(16):
        q.remove(output=outs[i])

    def check_q_multi_override_newest(_outs: list = outs) -> None:
        # Stored: [1..15, 20] (front -> back, since each push past full
        # replaced the back slot, ending with 20).
        expected = list(range(1, 16)) + [20]
        for i, want in enumerate(expected):
            got = int(ctx.get(_outs[i]))
            assert got == want, (
                f'q multi-override_newest deq {i}: got {got}, want {want}'
            )

    ctx.assert_all(check_q_multi_override_newest)


# Queue's override_oldest works even when real_capacity doesn't tile evenly,
# unlike IntStack which requires the exact match.
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(10)]
    q = IntQueue(
        holder=lambda i: PlayerStat(f'eq{i}').as_long(),
        counter=counter,
        most=255,
        capacity=10,
        capacity_is_exact=True,
        on_overflow='override_oldest',
    )
    for i in range(15):  # values 1..5 dropped, 6..15 survive
        q.add(i + 1)
    for i in range(10):
        q.remove(output=outs[i])

    def check_q_override_exact(_outs: list = outs) -> None:
        for i in range(10):
            got = int(ctx.get(_outs[i]))
            want = i + 6
            assert got == want, f'q-override-exact deq {i}: got {got}, want {want}'

    ctx.assert_all(check_q_override_exact)


# === Multi-holder cascade ===

with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(14)]
    q = IntQueue(
        holder=lambda i: PlayerStat(f'mq{i}').as_long(),
        counter=counter,
        most=255,
        capacity=14,
    )
    for i in range(14):
        q.add(i + 1)
    for i in range(14):
        q.remove(output=outs[i])

    def check_q_cascade(_outs: list = outs) -> None:
        for i in range(14):
            got = int(ctx.get(_outs[i]))
            want = i + 1
            assert got == want, f'q-cascade deq {i}: got {got}, want {want}'

    ctx.assert_all(check_q_cascade)


# Multi-holder + override_oldest. Queue's override_oldest doesn't require
# real_capacity to tile evenly, so capacity_is_exact pins it to 14.
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(14)]
    q = IntQueue(
        holder=lambda i: PlayerStat(f'oq{i}').as_long(),
        counter=counter,
        most=255,
        capacity=14,
        capacity_is_exact=True,
        on_overflow='override_oldest',
    )
    for i in range(20):  # values 1..6 dropped, 7..20 survive
        q.add(i + 1)
    for i in range(14):
        q.remove(output=outs[i])

    def check_q_multi_override(_outs: list = outs) -> None:
        for i in range(14):
            got = int(ctx.get(_outs[i]))
            want = i + 7  # FIFO of [7..20]
            assert got == want, f'q-multi-override deq {i}: got {got}, want {want}'

    ctx.assert_all(check_q_multi_override)


# === Width > 1 ===

with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [
        (PlayerStat(f'oa{i}').as_long(), PlayerStat(f'ob{i}').as_long())
        for i in range(3)
    ]
    q = IntQueue(
        holder=(PlayerStat('qa').as_long(), PlayerStat('qb').as_long()),
        counter=counter,
        most=1023,
    )
    q.add((1, 100))
    q.add((2, 200))
    q.add((3, 300))
    for i in range(3):
        q.remove(output=outs[i])

    def check_q_width2(_outs: list = outs) -> None:
        expected = [(1, 100), (2, 200), (3, 300)]
        for i, (oa, ob) in enumerate(_outs):
            got = (int(ctx.get(oa)), int(ctx.get(ob)))
            assert got == expected[i], (
                f'q-width2 deq {i}: got {got}, want {expected[i]}'
            )

    ctx.assert_all(check_q_width2)


# Width > 1 + multi-holder
with ExecutionContext(ignore_action_limits=True) as ctx:
    counter = PlayerStat('c').as_long()
    outs = [
        (PlayerStat(f'wqa{i}').as_long(), PlayerStat(f'wqb{i}').as_long())
        for i in range(12)
    ]
    q = IntQueue(
        holder=(
            lambda i: PlayerStat(f'wqha{i}').as_long(),
            lambda i: PlayerStat(f'wqhb{i}').as_long(),
        ),
        counter=counter,
        most=1023,
        capacity=12,
    )
    for i in range(12):
        q.add((i + 1, (i + 1) * 10))
    for i in range(12):
        q.remove(output=outs[i])

    def check_q_width2_multi(_outs: list = outs) -> None:
        for i in range(12):
            n = i + 1
            got = (int(ctx.get(_outs[i][0])), int(ctx.get(_outs[i][1])))
            want = (n, n * 10)
            assert got == want, f'q-width2-multi deq {i}: got {got}, want {want}'

    ctx.assert_all(check_q_width2_multi)


# === Failure cases ===

# most < 1 -> assertion
with expect_exception(AssertionError):
    IntQueue(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=0,
    )

# capacity == 0 -> ValueError
with expect_exception(ValueError):
    IntQueue(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=0,
    )

# Single Stat for queue needing multiple holders -> duplicate detection.
with expect_exception(ValueError):
    IntQueue(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=14,
    )

# Empty holder list -> ValueError
with expect_exception(ValueError):
    IntQueue(
        holder=[],
        counter=PlayerStat('c').as_long(),
        most=255,
    )

# Wrong-length enqueue
with expect_exception(ValueError):
    q = IntQueue(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    q.add((1, 2))

# Wrong-length dequeue output
with expect_exception(ValueError):
    q = IntQueue(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    q.remove(output=(PlayerStat('a').as_long(), PlayerStat('b').as_long()))

# Enqueue value out of range (negative)
with expect_exception(ValueError):
    q = IntQueue(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    q.add(-1)

# Enqueue value out of range (above most)
with expect_exception(ValueError):
    q = IntQueue(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    q.add(256)


# ===========================================================================
# Stack (plain, one Stat per slot)
# ===========================================================================

# Push then pop returns the most recent value.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'sh{i}').as_long() for i in range(4)]
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    s = Stack(holders=holders, counter=counter)
    s.add(42)
    s.add(7)
    s.remove(output=out)

    def check_stack_top() -> None:
        assert int(ctx.get(out)) == 7

    ctx.assert_all(check_stack_top)


# Push N values, pop them all in LIFO order. Capacity = N.
for _n in (1, 4, 8):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        holders = [PlayerStat(f'h{i}').as_long() for i in range(_n)]
        counter = PlayerStat('c').as_long()
        outs = [PlayerStat(f'o{i}').as_long() for i in range(_n)]
        s = Stack(holders=holders, counter=counter)
        for i in range(_n):
            s.add((i + 1) * 11)
        for i in range(_n):
            s.remove(output=outs[i])

        def check_stack_lifo(_count: int = _n, _outs: list = outs) -> None:
            for i in range(_count):
                got = int(ctx.get(_outs[i]))
                want = (_count - i) * 11
                assert got == want, f'Stack pop {i}: got {got}, want {want}'

        ctx.assert_all(check_stack_lifo)


# Pop on an empty Stack leaves output unchanged (no -1 sentinel since the
# slot type is arbitrary). Counter doesn't go negative either.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(3)]
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(out, 999, ignore_warning=True)
    s = Stack(holders=holders, counter=counter)
    s.remove(output=out)

    def check_stack_empty() -> None:
        assert int(ctx.get(out)) == 999  # untouched
        assert int(ctx.get(counter)) == 0

    ctx.assert_all(check_stack_empty)


# Plain Stack with `if_empty` set to a HousingType value writes that to
# the output on empty pop. Default behavior (None) is to leave it alone.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(3)]
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(out, 100, ignore_warning=True)
    s = Stack(holders=holders, counter=counter, if_empty=-99)
    s.remove(output=out)

    def check_stack_if_empty() -> None:
        assert int(ctx.get(out)) == -99

    ctx.assert_all(check_stack_if_empty)


# Plain Stack `if_empty` as a Callable runs in the Else context.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(3)]
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    flag = PlayerStat('flag').as_long()
    ctx.put(out, 5, ignore_warning=True)

    def on_empty_stack() -> None:
        flag.value = 7

    s = Stack(holders=holders, counter=counter, if_empty=on_empty_stack)
    s.remove(output=out)

    def check_stack_callable_empty() -> None:
        assert int(ctx.get(flag)) == 7
        assert int(ctx.get(out)) == 5

    ctx.assert_all(check_stack_callable_empty)


# Plain Stack `if_present` runs on successful pop. Per-call override
# can also suppress it with None.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(3)]
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    pops = PlayerStat('pops').as_long()

    def on_pop_stack() -> None:
        pops.value += 1

    s = Stack(holders=holders, counter=counter, if_present=on_pop_stack)
    s.add(1)
    s.add(2)
    s.add(3)
    s.remove(output=out)  # success -> pops=1
    s.remove(output=out, if_present=None)  # success but suppressed
    s.remove(output=out)  # success -> pops=2

    def check_stack_if_present() -> None:
        assert int(ctx.get(pops)) == 2

    ctx.assert_all(check_stack_if_present)


# Counter tracks current depth.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(5)]
    counter = PlayerStat('c').as_long()
    s = Stack(holders=holders, counter=counter)
    s.add(1)
    s.add(2)
    s.add(3)

    def check_stack_counter() -> None:
        assert int(ctx.get(counter)) == 3

    ctx.assert_all(check_stack_counter)


# 'ignore': pushes past capacity are no-ops; the original 4 survive.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(4)]
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(4)]
    s = Stack(holders=holders, counter=counter, on_overflow='ignore')
    for i in range(7):  # 4 successful, 3 ignored
        s.add(i + 1)
    for i in range(4):
        s.remove(output=outs[i])

    def check_stack_ignore(_outs: list = outs) -> None:
        for i, want in enumerate([4, 3, 2, 1]):
            got = int(ctx.get(_outs[i]))
            assert got == want, f'Stack ignore pop {i}: got {got}, want {want}'

    ctx.assert_all(check_stack_ignore)


# 'override_oldest': drops the bottom and shifts up.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(4)]
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(4)]
    s = Stack(holders=holders, counter=counter, on_overflow='override_oldest')
    for i in range(7):  # values 1..3 dropped, 4..7 survive
        s.add(i + 1)
    for i in range(4):
        s.remove(output=outs[i])

    def check_stack_override_oldest(_outs: list = outs) -> None:
        for i, want in enumerate([7, 6, 5, 4]):
            got = int(ctx.get(_outs[i]))
            assert got == want, f'Stack override_oldest pop {i}: got {got}, want {want}'

    ctx.assert_all(check_stack_override_oldest)


# 'override_newest': replaces the top in place when full.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(4)]
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(4)]
    s = Stack(holders=holders, counter=counter, on_overflow='override_newest')
    for i in range(7):  # 1..4 fill; 5, 6, 7 each replace the top
        s.add(i + 1)
    for i in range(4):
        s.remove(output=outs[i])

    def check_stack_override_newest(_outs: list = outs) -> None:
        # Stored: [7, 3, 2, 1] (top to bottom). Pop order: 7, 3, 2, 1.
        for i, want in enumerate([7, 3, 2, 1]):
            got = int(ctx.get(_outs[i]))
            assert got == want, f'Stack override_newest pop {i}: got {got}, want {want}'

    ctx.assert_all(check_stack_override_newest)


# Width > 1 with mixed-type holders: each width-position is a separate Stat.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [
        (PlayerStat(f'a{i}').as_long(), PlayerStat(f'b{i}').as_long()) for i in range(3)
    ]
    counter = PlayerStat('c').as_long()
    outs = [
        (PlayerStat(f'oa{i}').as_long(), PlayerStat(f'ob{i}').as_long())
        for i in range(3)
    ]
    s = Stack(holders=holders, counter=counter)
    s.add((1, 100))
    s.add((2, 200))
    s.add((3, 300))
    for i in range(3):
        s.remove(output=outs[i])

    def check_stack_width2(_outs: list = outs) -> None:
        expected = [(3, 300), (2, 200), (1, 100)]
        for i, (oa, ob) in enumerate(_outs):
            got = (int(ctx.get(oa)), int(ctx.get(ob)))
            assert got == expected[i], (
                f'Stack width-2 pop {i}: got {got}, want {expected[i]}'
            )

    ctx.assert_all(check_stack_width2)


# Plain Stack works with non-int types — string holders, string values.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'sh{i}').as_string() for i in range(3)]
    counter = PlayerStat('c').as_long()
    str_outs = [PlayerStat(f'so{i}').as_string() for i in range(3)]
    s = Stack(holders=holders, counter=counter)
    s.add('alpha')
    s.add('beta')
    s.add('gamma')
    for i in range(3):
        s.remove(output=str_outs[i])

    def check_stack_string() -> None:
        assert str(ctx.get(str_outs[0])) == 'gamma'
        assert str(ctx.get(str_outs[1])) == 'beta'
        assert str(ctx.get(str_outs[2])) == 'alpha'

    ctx.assert_all(check_stack_string)


# === Stack failure cases ===

# Empty holders -> ValueError
with expect_exception(ValueError):
    Stack(holders=[], counter=PlayerStat('c').as_long())

# Duplicate stat in holders -> ValueError
with expect_exception(ValueError):
    dup = PlayerStat('dup').as_long()
    Stack(holders=[dup, dup], counter=PlayerStat('c').as_long())

# Mismatched widths between holder groups -> ValueError (from assert_same_widths)
with expect_exception(ValueError):
    Stack(
        holders=[
            PlayerStat('a').as_long(),
            (PlayerStat('b').as_long(), PlayerStat('c').as_long()),
        ],
        counter=PlayerStat('c').as_long(),
    )

# Wrong-length push value
with expect_exception(ValueError):
    s = Stack(
        holders=[PlayerStat(f'h{i}').as_long() for i in range(3)],
        counter=PlayerStat('c').as_long(),
    )
    s.add((1, 2))

# Wrong-length pop output
with expect_exception(ValueError):
    s = Stack(
        holders=[PlayerStat(f'h{i}').as_long() for i in range(3)],
        counter=PlayerStat('c').as_long(),
    )
    s.remove(output=(PlayerStat('a').as_long(), PlayerStat('b').as_long()))


# ===========================================================================
# Queue (plain, one Stat per slot)
# ===========================================================================

# Enqueue then dequeue returns the OLDEST value.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'qh{i}').as_long() for i in range(4)]
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    q = Queue(holders=holders, counter=counter)
    q.add(42)
    q.add(7)
    q.remove(output=out)

    def check_queue_front() -> None:
        assert int(ctx.get(out)) == 42

    ctx.assert_all(check_queue_front)


# Enqueue N values, dequeue in FIFO order.
for _n in (1, 4, 8):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        holders = [PlayerStat(f'h{i}').as_long() for i in range(_n)]
        counter = PlayerStat('c').as_long()
        outs = [PlayerStat(f'o{i}').as_long() for i in range(_n)]
        q = Queue(holders=holders, counter=counter)
        for i in range(_n):
            q.add((i + 1) * 11)
        for i in range(_n):
            q.remove(output=outs[i])

        def check_queue_fifo(_count: int = _n, _outs: list = outs) -> None:
            for i in range(_count):
                got = int(ctx.get(_outs[i]))
                want = (i + 1) * 11
                assert got == want, f'Queue dequeue {i}: got {got}, want {want}'

        ctx.assert_all(check_queue_fifo)


# Dequeue on empty leaves output unchanged.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(3)]
    counter = PlayerStat('c').as_long()
    out = PlayerStat('out').as_long()
    ctx.put(out, 999, ignore_warning=True)
    q = Queue(holders=holders, counter=counter)
    q.remove(output=out)

    def check_queue_empty() -> None:
        assert int(ctx.get(out)) == 999
        assert int(ctx.get(counter)) == 0

    ctx.assert_all(check_queue_empty)


# Interleaved enqueue/dequeue keeps FIFO order.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(3)]
    counter = PlayerStat('c').as_long()
    out_a = PlayerStat('oa').as_long()
    out_b = PlayerStat('ob').as_long()
    out_c = PlayerStat('oc').as_long()
    q = Queue(holders=holders, counter=counter)
    q.add(11)
    q.add(22)
    q.remove(output=out_a)  # 11
    q.add(33)
    q.remove(output=out_b)  # 22
    q.remove(output=out_c)  # 33

    def check_queue_interleave() -> None:
        assert int(ctx.get(out_a)) == 11
        assert int(ctx.get(out_b)) == 22
        assert int(ctx.get(out_c)) == 33
        assert int(ctx.get(counter)) == 0

    ctx.assert_all(check_queue_interleave)


# 'ignore': enqueue past capacity is a no-op; original 4 survive in order.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(4)]
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(4)]
    q = Queue(holders=holders, counter=counter, on_overflow='ignore')
    for i in range(7):
        q.add(i + 1)
    for i in range(4):
        q.remove(output=outs[i])

    def check_queue_ignore(_outs: list = outs) -> None:
        for i, want in enumerate([1, 2, 3, 4]):
            got = int(ctx.get(_outs[i]))
            assert got == want, f'Queue ignore deq {i}: got {got}, want {want}'

    ctx.assert_all(check_queue_ignore)


# 'override_oldest': drop front, shift down, write new at back.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(4)]
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(4)]
    q = Queue(holders=holders, counter=counter, on_overflow='override_oldest')
    for i in range(7):  # 1..3 dropped, 4..7 survive
        q.add(i + 1)
    for i in range(4):
        q.remove(output=outs[i])

    def check_queue_override_oldest(_outs: list = outs) -> None:
        for i, want in enumerate([4, 5, 6, 7]):
            got = int(ctx.get(_outs[i]))
            assert got == want, f'Queue override_oldest deq {i}: got {got}, want {want}'

    ctx.assert_all(check_queue_override_oldest)


# 'override_newest': replace the back slot in place.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'h{i}').as_long() for i in range(4)]
    counter = PlayerStat('c').as_long()
    outs = [PlayerStat(f'o{i}').as_long() for i in range(4)]
    q = Queue(holders=holders, counter=counter, on_overflow='override_newest')
    for i in range(7):  # 1..4 fill, then 5, 6, 7 each replace the back
        q.add(i + 1)
    for i in range(4):
        q.remove(output=outs[i])

    def check_queue_override_newest(_outs: list = outs) -> None:
        # Stored: [1, 2, 3, 7] front -> back.
        for i, want in enumerate([1, 2, 3, 7]):
            got = int(ctx.get(_outs[i]))
            assert got == want, f'Queue override_newest deq {i}: got {got}, want {want}'

    ctx.assert_all(check_queue_override_newest)


# Width > 1 queue.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [
        (PlayerStat(f'qa{i}').as_long(), PlayerStat(f'qb{i}').as_long())
        for i in range(3)
    ]
    counter = PlayerStat('c').as_long()
    outs = [
        (PlayerStat(f'oa{i}').as_long(), PlayerStat(f'ob{i}').as_long())
        for i in range(3)
    ]
    q = Queue(holders=holders, counter=counter)
    q.add((1, 100))
    q.add((2, 200))
    q.add((3, 300))
    for i in range(3):
        q.remove(output=outs[i])

    def check_queue_width2(_outs: list = outs) -> None:
        expected = [(1, 100), (2, 200), (3, 300)]
        for i, (oa, ob) in enumerate(_outs):
            got = (int(ctx.get(oa)), int(ctx.get(ob)))
            assert got == expected[i], (
                f'Queue width-2 deq {i}: got {got}, want {expected[i]}'
            )

    ctx.assert_all(check_queue_width2)


# String values through a plain Queue.
with ExecutionContext(ignore_action_limits=True) as ctx:
    holders = [PlayerStat(f'qs{i}').as_string() for i in range(3)]
    counter = PlayerStat('c').as_long()
    qstr_outs = [PlayerStat(f'qso{i}').as_string() for i in range(3)]
    q = Queue(holders=holders, counter=counter)
    q.add('first')
    q.add('second')
    q.add('third')
    for i in range(3):
        q.remove(output=qstr_outs[i])

    def check_queue_string() -> None:
        assert str(ctx.get(qstr_outs[0])) == 'first'
        assert str(ctx.get(qstr_outs[1])) == 'second'
        assert str(ctx.get(qstr_outs[2])) == 'third'

    ctx.assert_all(check_queue_string)


# === Queue failure cases ===

with expect_exception(ValueError):
    Queue(holders=[], counter=PlayerStat('c').as_long())

with expect_exception(ValueError):
    dup = PlayerStat('dup').as_long()
    Queue(holders=[dup, dup], counter=PlayerStat('c').as_long())

with expect_exception(ValueError):
    q = Queue(
        holders=[PlayerStat(f'h{i}').as_long() for i in range(3)],
        counter=PlayerStat('c').as_long(),
    )
    q.add((1, 2))

with expect_exception(ValueError):
    q = Queue(
        holders=[PlayerStat(f'h{i}').as_long() for i in range(3)],
        counter=PlayerStat('c').as_long(),
    )
    q.remove(output=(PlayerStat('a').as_long(), PlayerStat('b').as_long()))
