"""approximate_sqrt from pyhtsw.ext: result close to math.sqrt for several inputs."""

import math
import random

from helpers import expect_exception

from pyhtsw import ExecutionContext, PlayerStat
from pyhtsw.ext import approximate_sqrt


def assert_sqrt_close(v: float) -> None:
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_double()
        result = PlayerStat('result').as_double()
        ctx.put(x, v)
        approximate_sqrt(x, assign_to=result)

    actual = float(ctx.get_raw(result))
    expected = math.sqrt(v)
    err = abs(actual - expected)
    assert err < 0.01, f'sqrt({v}): got {actual}, expected {expected}, err={err}'


for _ in range(20):
    assert_sqrt_close(random.uniform(0.01, 10_000.0))


# Cannot assign to the same stat as input
with expect_exception(ValueError):
    with ExecutionContext():
        x = PlayerStat('x').as_double()
        approximate_sqrt(x, assign_to=x)
