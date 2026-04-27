"""approximate_sqrt from pyhtsl.ext: result close to math.sqrt for several inputs."""

import math
import random

from pyhtsl import ExecutionContext, PlayerStat
from pyhtsl.ext import approximate_sqrt


def assert_sqrt_close(v: float) -> None:
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_double()
        result = PlayerStat('result').as_double()
        ctx.put(x, v)
        approximate_sqrt(x, assign_to=result)

        def check() -> None:
            actual = float(ctx.get_raw(result))
            expected = math.sqrt(v)
            err = abs(actual - expected)
            assert err < 0.01, (
                f'sqrt({v}): got {actual}, expected {expected}, err={err}'
            )

        ctx.assert_all(check)


for _ in range(20):
    assert_sqrt_close(random.uniform(0.01, 10_000.0))


# Cannot assign to the same stat as input
raised = False
try:
    with ExecutionContext():
        x = PlayerStat('x').as_double()
        approximate_sqrt(x, assign_to=x)
except ValueError:
    raised = True
assert raised, 'expected ValueError when assign_to == input'
