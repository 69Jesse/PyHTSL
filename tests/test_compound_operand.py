"""A CompoundExpression used as an operand flattens into the surrounding computation."""

import math

from pyhtsw import (
    Container,
    ExecutionContext,
    IfAll,
    PlayerPositionX,
    PlayerPositionY,
    PlayerPositionZ,
    PlayerStat,
    chat,
)

# Squared distance built from `**` and `+`
with Container() as container:
    x = PlayerStat('x').as_double()
    y = PlayerStat('y').as_double()
    z = PlayerStat('z').as_double()
    distance_squared = (
        (x - PlayerPositionX.as_double()) ** 2
        + (y - PlayerPositionY.as_double()) ** 2
        + (z - PlayerPositionZ.as_double()) ** 2
    )
    with IfAll(distance_squared > 1000):
        chat('hi')

expected = (
    'var "tmp0" = "%var.player/x 0.0%D" false\n'
    'var "tmp0" -= "%player.pos.x%D" false\n'
    'var "tmp0" *= "%var.player/tmp0 0.0%D" false\n'
    'var "tmp1" = "%var.player/y 0.0%D" false\n'
    'var "tmp1" -= "%player.pos.y%D" false\n'
    'var "tmp1" *= "%var.player/tmp1 0.0%D" false\n'
    'var "tmp0" += "%var.player/tmp1 0.0%D" false\n'
    'var "tmp2" = "%var.player/z 0.0%D" false\n'
    'var "tmp2" -= "%player.pos.z%D" false\n'
    'var "tmp2" *= "%var.player/tmp2 0.0%D" false\n'
    'var "tmp0" += "%var.player/tmp2 0.0%D" false\n'
    'if and (var "tmp0" > 1000.0 0.0) {\n'
    '    chat "hi"\n'
    '}'
)
assert container.into_htsl() == expected, container.into_htsl()


# sum(...) seeds with the integer 0 but must match the `+` chain
with Container() as sum_container:
    x = PlayerStat('x').as_double()
    y = PlayerStat('y').as_double()
    z = PlayerStat('z').as_double()
    distance_squared = sum(
        (
            (x - PlayerPositionX.as_double()) ** 2,
            (y - PlayerPositionY.as_double()) ** 2,
            (z - PlayerPositionZ.as_double()) ** 2,
        ),
    )
    with IfAll(distance_squared > 1000):
        chat('hi')

assert sum_container.into_htsl() == expected, sum_container.into_htsl()


# A compound as the operand of an assignment
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    out = PlayerStat('out').as_long()
    out.value = (x - 1) ** 2 + (y - 1) ** 2

expected = (
    'var "out" = "%var.player/x 0%L" true\n'
    'var "out" -= 1 true\n'
    'var "out" *= "%var.player/out 0%L" true\n'
    'var "tmp0" = "%var.player/y 0%L" false\n'
    'var "tmp0" -= 1 false\n'
    'var "tmp0" *= "%var.player/tmp0 0%L" false\n'
    'var "out" += "%var.player/tmp0 0%L" true'
)
assert container.into_htsl() == expected, container.into_htsl()


# Two coexisting temps in a condition must keep distinct numbers
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    c = PlayerStat('c').as_long()
    d = PlayerStat('d').as_long()
    with IfAll((a * b + c * d) > 1000):
        chat('hi')

expected = (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" *= "%var.player/b 0%L" false\n'
    'var "tmp1" = "%var.player/c 0%L" false\n'
    'var "tmp1" *= "%var.player/d 0%L" false\n'
    'var "tmp0" += "%var.player/tmp1 0%L" false\n'
    'if and (var "tmp0" > 1000 0) {\n'
    '    chat "hi"\n'
    '}'
)
assert container.into_htsl() == expected, container.into_htsl()


# A compound used directly (not wrapped) as a condition's lhs
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    with IfAll(a.remainder(b) > 5):
        chat('hi')

expected = (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" /= "%var.player/b 0%L" false\n'
    'var "tmp0" *= "%var.player/b 0%L" false\n'
    'var "tmp1" = "%var.player/a 0%L" false\n'
    'var "tmp1" -= "%var.player/tmp0 0%L" false\n'
    'if and (var "tmp1" > 5 0) {\n'
    '    chat "hi"\n'
    '}'
)
assert container.into_htsl() == expected, container.into_htsl()


# A nested rhs that references the lhs keeps the prior write alive
with Container() as container:
    x = PlayerStat('x').as_long()
    a = PlayerStat('a').as_long()
    x.value = 5
    x.value = (x + a) ** 2

expected = (
    'var "x" = 5 true\n'
    'var "x" += "%var.player/a 0%L" true\n'
    'var "x" *= "%var.player/x 0%L" true'
)
assert container.into_htsl() == expected, container.into_htsl()


# Two conditions with a computed lhs each keep their own computation
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    with IfAll((a * b) > 1000):
        chat('one')
    with IfAll((a * b) > 2000):
        chat('two')

one_block = (
    'var "tmp0" = "%var.player/a 0%L" false\nvar "tmp0" *= "%var.player/b 0%L" false\n'
)
expected = (
    one_block
    + 'if and (var "tmp0" > 1000 0) {\n    chat "one"\n}\n'
    + one_block
    + 'if and (var "tmp0" > 2000 0) {\n    chat "two"\n}'
)
assert container.into_htsl() == expected, container.into_htsl()


# Two computed conditions each evaluate independently
with ExecutionContext() as ctx:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    low = PlayerStat('low').as_long()
    high = PlayerStat('high').as_long()
    ctx.put(a, 40, ignore_warning=True)
    ctx.put(b, 40, ignore_warning=True)
    low.value = 0
    high.value = 0
    with IfAll((a * b) > 1000):
        low.value = 1
    with IfAll((a * b) > 2000):
        high.value = 1

assert int(ctx.get_raw(low)) == 1, ctx.get_raw(low)
assert int(ctx.get_raw(high)) == 0, ctx.get_raw(high)


# The squared distance computes the right number
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_double()
    y = PlayerStat('y').as_double()
    z = PlayerStat('z').as_double()
    out = PlayerStat('out').as_double()
    ctx.put(x, 10.0, ignore_warning=True)
    ctx.put(y, 5.0, ignore_warning=True)
    ctx.put(z, 2.0, ignore_warning=True)
    out.value = (x - 1.0) ** 2 + (y - 1.0) ** 2 + (z - 1.0) ** 2

actual = float(ctx.get_raw(out))
expected_value = (10 - 1) ** 2 + (5 - 1) ** 2 + (2 - 1) ** 2
assert actual == expected_value, f'got {actual}, expected {expected_value}'


# The sum(...) form computes the same number
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_double()
    y = PlayerStat('y').as_double()
    z = PlayerStat('z').as_double()
    out = PlayerStat('out').as_double()
    ctx.put(x, 10.0, ignore_warning=True)
    ctx.put(y, 5.0, ignore_warning=True)
    ctx.put(z, 2.0, ignore_warning=True)
    out.value = sum(((x - 1.0) ** 2, (y - 1.0) ** 2, (z - 1.0) ** 2))

actual = float(ctx.get_raw(out))
assert actual == expected_value, f'got {actual}, expected {expected_value}'


# A multi-temp compound inside a condition branches right
for a_val, hit in ((30, 1), (1, 0)):
    with ExecutionContext() as ctx:
        a = PlayerStat('a').as_long()
        b = PlayerStat('b').as_long()
        c = PlayerStat('c').as_long()
        d = PlayerStat('d').as_long()
        flag = PlayerStat('flag').as_long()
        ctx.put(a, a_val, ignore_warning=True)
        ctx.put(b, 40, ignore_warning=True)
        ctx.put(c, 2, ignore_warning=True)
        ctx.put(d, 3, ignore_warning=True)
        flag.value = 0
        with IfAll((a * b + c * d) > 1000):
            flag.value = 1

    actual = int(ctx.get_raw(flag))
    expected_flag = 1 if (a_val * 40 + 2 * 3) > 1000 else 0
    assert actual == expected_flag == hit, f'a={a_val}: got {actual}'


# A nested rhs self reference is not lost
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_long()
    a = PlayerStat('a').as_long()
    ctx.put(a, 3, ignore_warning=True)
    x.value = 5
    x.value = (x + a) ** 2

actual = int(ctx.get_raw(x))
assert actual == (5 + 3) ** 2, f'got {actual}, expected {(5 + 3) ** 2}'


# A compound built on a computed base, with a self-referencing `%` assignment
for deg in (10.0, 145.0, 235.0, -200.0):
    with ExecutionContext() as ctx:
        raw = PlayerStat('raw').as_double()
        folded = PlayerStat('folded').as_double()
        ctx.put(raw, deg, ignore_warning=True)
        folded.value = raw % 360.0
        folded.value = folded + 90.0
        folded.value = folded % 180.0 - 90.0

    actual = float(ctx.get_raw(folded))
    expected_value = ((deg % 360.0) + 90.0) % 180.0 - 90.0
    assert math.isclose(actual, expected_value, abs_tol=1e-3), (
        f'deg={deg}: got {actual}, expected {expected_value}'
    )
