from typing import Literal, overload

from ..actions.conditional.statements import Else, IfAll
from ..checkable import Checkable
from ..editable import Editable
from ..stats.player_stat import PlayerStat
from ..stats.stat import Stat

__all__ = (
    'approximate_sqrt',
    'approximate_sin_cos',
)


SQRT_INV_SCALAR = 1000.0
SQRT_SCALAR = 1.0 / SQRT_INV_SCALAR


@overload
def approximate_sqrt(
    x: Checkable,
    *,
    assign_to: Editable,
    can_modify_x: Literal[False] = False,
) -> None: ...


@overload
def approximate_sqrt(
    x: Editable,
    *,
    assign_to: Editable,
    can_modify_x: Literal[True],
) -> None: ...


@overload
def approximate_sqrt(
    x: Editable,
    *,
    assign_to: Editable,
    can_modify_x: bool = False,
) -> None: ...


def approximate_sqrt(
    x: Checkable,
    *,
    assign_to: Editable,
    can_modify_x: bool = False,
) -> None:
    if x.equals(assign_to):
        raise ValueError('Cannot assign to the same stat as input')

    temp0 = PlayerStat('tmp0').as_double().without_auto_unset()
    temp1 = PlayerStat('tmp1').as_double().without_auto_unset()
    temp2 = PlayerStat('tmp2').as_double().without_auto_unset()
    temp3 = PlayerStat('tmp3').as_double().without_auto_unset()
    if not can_modify_x:
        x_or_temp4 = PlayerStat('tmp4').as_double().without_auto_unset()
    else:
        assert isinstance(x, Editable)
        x_or_temp4 = x.as_double()
        if isinstance(x_or_temp4, Stat):
            x_or_temp4 = x_or_temp4.without_auto_unset()

    assign_to = assign_to.as_double()

    temp0.value = 3037000498.0 * SQRT_SCALAR
    temp0.value /= x
    temp0.value += 1.0 * SQRT_SCALAR  # this doesn't seem to do much heh

    x_or_temp4.value = x
    x_or_temp4.value *= temp0
    x_or_temp4.value *= temp0

    temp1.value = x_or_temp4
    temp1.value /= 537752656.0
    temp1.value += 880298.0 * SQRT_SCALAR**2

    temp2.value = x_or_temp4
    temp2.value /= temp1
    temp2.value /= SQRT_INV_SCALAR**2  # can maybe take this line out somehow
    temp2.value += temp1

    temp1.value = x_or_temp4
    temp1.value /= temp2
    temp2.value *= 0.25 * SQRT_INV_SCALAR**2
    temp2.value += temp1

    temp3.value = x_or_temp4
    temp3.value /= temp2
    temp2.value /= SQRT_INV_SCALAR**2  # can maybe take this line out somehow
    temp3.value += temp2

    temp1.value = x_or_temp4
    temp1.value /= temp3
    temp3.value *= 0.25 * SQRT_INV_SCALAR
    temp1.value /= SQRT_INV_SCALAR  # can maybe take this line out somehow
    temp3.value += temp1

    assign_to.value = x_or_temp4
    assign_to.value /= temp3
    assign_to.value += temp3

    x_or_temp4.value /= assign_to
    assign_to.value /= 4.0
    assign_to.value += x_or_temp4

    assign_to.value += 1.0 * SQRT_SCALAR
    assign_to.value /= temp0


@overload
def approximate_sin_cos(
    x: Checkable,
    *,
    assign_to_sin: Editable,
    assign_to_cos: Editable,
    can_modify_x: Literal[False] = False,
    certain_x_in_range: Literal[90, 180] | None = None,
    sin_sign: Literal[1, -1] = 1,
    cos_sign: Literal[1, -1] = 1,
) -> None: ...


@overload
def approximate_sin_cos(
    x: Editable,
    *,
    assign_to_sin: Editable,
    assign_to_cos: Editable,
    can_modify_x: Literal[True],
    certain_x_in_range: Literal[90, 180] | None = None,
    sin_sign: Literal[1, -1] = 1,
    cos_sign: Literal[1, -1] = 1,
) -> None: ...


@overload
def approximate_sin_cos(
    x: Editable,
    *,
    assign_to_sin: Editable,
    assign_to_cos: Editable,
    can_modify_x: bool = False,
    certain_x_in_range: Literal[90, 180] | None = None,
    sin_sign: Literal[1, -1] = 1,
    cos_sign: Literal[1, -1] = 1,
) -> None: ...


def approximate_sin_cos(
    x: Checkable,
    *,
    assign_to_sin: Editable,
    assign_to_cos: Editable,
    can_modify_x: bool = False,
    certain_x_in_range: Literal[90, 180] | None = None,
    sin_sign: Literal[1, -1] = 1,
    cos_sign: Literal[1, -1] = 1,
) -> None:
    """
    Approximate sine and cosine at the same time, AMAZINGLY BLAZINGLY EPIC GAMERLY fast

    Assumes x is in degrees,
    if you're certain x is in the range of [-90, 90] or [-180, 180],
    you may set certain_x_in_range to 90 or 180 respectively.
    """

    x = x.as_double()
    temp0 = PlayerStat('tmp0').as_double().without_auto_unset()
    if not can_modify_x:
        x_or_temp1 = PlayerStat('tmp1').as_double().without_auto_unset()
    else:
        assert isinstance(x, Editable)
        x_or_temp1 = x.as_double()
        if isinstance(x_or_temp1, Stat):
            x_or_temp1 = x_or_temp1.without_auto_unset()
    original_x = (
        PlayerStat('tmp1' if can_modify_x else 'tmp2')
        .as_double()
        .without_auto_unset()
    )

    if certain_x_in_range != 90:
        if certain_x_in_range != 180:
            original_x.value = x % 360.0
            x_or_temp1.value = original_x + 90.0
            x_or_temp1.value = x_or_temp1 % 180.0 - 90.0
        else:
            with IfAll(x >= 0.0):
                original_x.value = x
            with Else:
                original_x.value = x + 360.0
            x_or_temp1.value = original_x + 90.0
            with IfAll(x_or_temp1 >= 180.0):
                x_or_temp1.value -= 180.0
            with IfAll(x_or_temp1 >= 180.0):
                x_or_temp1.value -= 270.0
            with Else:
                x_or_temp1.value -= 90.0
    else:
        x_or_temp1.value = x

    assign_to_sin.value = x_or_temp1
    x_or_temp1.value *= x_or_temp1
    temp0.value = 32400.0
    temp0.value += x_or_temp1
    if cos_sign == 1:
        assign_to_cos.value = 32400.0
    else:
        assign_to_cos.value = -32400.0
    x_or_temp1.value *= 4.0
    if cos_sign == 1:
        assign_to_cos.value -= x_or_temp1
    else:
        assign_to_cos.value += x_or_temp1
    assign_to_cos.value /= temp0.value
    x_or_temp1.value *= assign_to_sin
    x_or_temp1.value /= 5508000.0

    if sin_sign == 1:
        assign_to_sin.value *= 0.017
        assign_to_sin.value -= x_or_temp1
    else:
        assign_to_sin.value *= -0.017
        assign_to_sin.value += x_or_temp1

    if certain_x_in_range != 90:
        with IfAll(
            original_x >= 90.0,
            original_x < 270.0,
        ):
            assign_to_sin.value *= -1
            assign_to_cos.value *= -1
