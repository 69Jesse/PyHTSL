"""Computed expressions passed directly as an action argument materialize.

A `BinaryExpression` / `CompoundExpression` handed straight to an action (not
via an f-string) used to leak its deferred sentinel into the rendered HTSL,
because the deferred resolver only scanned string fields. It now materializes
those fields into temp stats, the same way f-string interpolation does.
"""

from pyhtsw import (
    Container,
    IfAll,
    Location,
    PlayerStat,
    change_velocity,
    launch_to_target,
)

# A single computed arg materializes into a temp the action then references
with Container() as container:
    x = PlayerStat('x').as_long()
    change_velocity(x + 1, 0, 0)

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/x 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'changeVelocity %var.player/tmp0 0% 0 0'
), container.into_htsl()


# Two computed args in one action get distinct temps
with Container() as container:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    change_velocity(x + 1, y * 2, 3)

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/x 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'var "tmp1" = "%var.player/y 0%L" false\n'
    'var "tmp1" *= 2 false\n'
    'changeVelocity %var.player/tmp0 0% %var.player/tmp1 0% 3'
), container.into_htsl()


# A compound expression (modulo) passed directly also materializes
with Container() as container:
    a = PlayerStat('a').as_long()
    change_velocity(a % 5, 0, 0)

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/a 0%L" false\n'
    'var "tmp0" /= 5 false\n'
    'var "tmp0" *= 5 false\n'
    'var "tmp1" = "%var.player/a 0%L" false\n'
    'var "tmp1" -= "%var.player/tmp0 0%L" false\n'
    'if and (var "tmp1" < 0 0) {\n'
    '    var "tmp1" += 5 false\n'
    '}\n'
    'changeVelocity %var.player/tmp1 0% 0 0'
), container.into_htsl()


# The computation lands inside the nested block when nested in a conditional
with Container() as container:
    x = PlayerStat('x').as_long()
    with IfAll(x > 0):
        change_velocity(x + 1, 0, 0)

assert container.into_htsl() == (
    'if and (var "x" > 0 0) {\n'
    '    var "tmp0" = "%var.player/x 0%L" false\n'
    '    var "tmp0" += 1 false\n'
    '    changeVelocity %var.player/tmp0 0% 0 0\n'
    '}'
), container.into_htsl()


# Mixed paths in one statement: a computed coordinate (string field) and a
# computed strength (direct field) share the materialize batch and get distinct
# temps
with Container() as container:
    x = PlayerStat('x').as_long()
    launch_to_target(Location.custom(x + 1, 0, 0), strength=x * 2)

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/x 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'var "tmp1" = "%var.player/x 0%L" false\n'
    'var "tmp1" *= 2 false\n'
    'launchTarget "custom_coordinates" "%var.player/tmp0 0% 0 0" %var.player/tmp1 0%'
), container.into_htsl()


# Temp numbers reset (reuse) across separate statements
with Container() as container:
    x = PlayerStat('x').as_long()
    change_velocity(x + 1, 0, 0)
    change_velocity(x + 2, 0, 0)

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/x 0%L" false\n'
    'var "tmp0" += 1 false\n'
    'changeVelocity %var.player/tmp0 0% 0 0\n'
    'var "tmp0" = "%var.player/x 0%L" false\n'
    'var "tmp0" += 2 false\n'
    'changeVelocity %var.player/tmp0 0% 0 0'
), container.into_htsl()


# A plain stat (not a computed expression) passes through untouched — no temp
with Container() as container:
    x = PlayerStat('x').as_long()
    change_velocity(x, 0, 0)

assert container.into_htsl() == 'changeVelocity %var.player/x 0% 0 0', (
    container.into_htsl()
)
