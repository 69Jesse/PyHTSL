"""approximate_sin_cos from pyhtsw.ext: results close to math.sin/cos for several inputs."""

import math
import random
from typing import Literal

from pyhtsw import ExecutionContext, PlayerStat
from pyhtsw.ext import approximate_sin_cos


def assert_sin_cos_close(
    deg: float,
    *,
    certain_x_in_range: Literal[90, 180] | None = None,
) -> None:
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_double()
        sin_out = PlayerStat('sin').as_double()
        cos_out = PlayerStat('cos').as_double()
        ctx.put(x, deg)
        approximate_sin_cos(
            x,
            assign_to_sin=sin_out,
            assign_to_cos=cos_out,
            certain_x_in_range=certain_x_in_range,
        )  # type: ignore

    actual_sin = float(ctx.get_raw(sin_out))
    actual_cos = float(ctx.get_raw(cos_out))
    expected_sin = math.sin(math.radians(deg))
    expected_cos = math.cos(math.radians(deg))
    err_sin = abs(actual_sin - expected_sin)
    err_cos = abs(actual_cos - expected_cos)
    assert err_sin < 0.02, (
        f'sin({deg}): got {actual_sin}, expected {expected_sin}, err={err_sin}'
    )
    assert err_cos < 0.02, (
        f'cos({deg}): got {actual_cos}, expected {expected_cos}, err={err_cos}'
    )


# Within [-90, 90] (no range adjustment needed)
for _ in range(15):
    assert_sin_cos_close(random.uniform(-90, 90), certain_x_in_range=90)


# Within [-180, 180] (uses one branch of the range adjustment)
for _ in range(15):
    assert_sin_cos_close(random.uniform(-180, 180), certain_x_in_range=180)


# Default range (uses mod-based adjustment for arbitrary input — covers
# multiple full revolutions on either side of zero)
for _ in range(20):
    assert_sin_cos_close(random.uniform(-720, 720))


# sin_sign / cos_sign flip the output
with ExecutionContext() as ctx:
    x = PlayerStat('x').as_double()
    sin_out = PlayerStat('sin').as_double()
    cos_out = PlayerStat('cos').as_double()
    ctx.put(x, 30.0)
    approximate_sin_cos(
        x,
        assign_to_sin=sin_out,
        assign_to_cos=cos_out,
        certain_x_in_range=90,
        sin_sign=-1,
        cos_sign=-1,
    )

# With sin_sign=-1 / cos_sign=-1 the output approximates -sin(30) / -cos(30).
actual_sin = float(ctx.get_raw(sin_out))
actual_cos = float(ctx.get_raw(cos_out))
assert abs(actual_sin - (-math.sin(math.radians(30)))) < 0.02, actual_sin
assert abs(actual_cos - (-math.cos(math.radians(30)))) < 0.02, actual_cos
