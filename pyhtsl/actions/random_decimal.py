import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('RandomDecimal',)


def RandomDecimal(
    lower_bound: float,
    exclusive_upper_bound: float,
) -> PlaceholderCheckable:
    key = f'%random.decimal/{lower_bound} {exclusive_upper_bound}%'
    return PlaceholderCheckable(
        assignment_right_side=f'{key}',
        comparison_left_side=f'placeholder "{key}"',
        comparison_right_side=f'{key}',
        in_string=f'{key}',
        constant_internal_type=InternalType.DOUBLE,
        backend_value=np.float64(0),
    )
