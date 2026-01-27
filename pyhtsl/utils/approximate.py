from pyhtsl import (
    PlayerStat,
    IfAnd,
    Else,
)
from pyhtsl.types import Editable, Checkable, BaseStat

from typing import Literal, overload


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

    temp1 = PlayerStat('temp1').as_double().without_automatic_unset()
    temp2 = PlayerStat('temp2').as_double().without_automatic_unset()
    temp3 = PlayerStat('temp3').as_double().without_automatic_unset()
    temp4 = PlayerStat('temp4').as_double().without_automatic_unset()
    if not can_modify_x:
        x_or_temp5 = PlayerStat('temp5').as_double().without_automatic_unset()
    else:
        assert isinstance(x, Editable)
        x_or_temp5 = x.as_double()
        if isinstance(x_or_temp5, BaseStat):
            x_or_temp5 = x_or_temp5.without_automatic_unset()

    assign_to = assign_to.as_double()

    temp1.value = 3037000498.0 * SQRT_SCALAR
    temp1.value /= x
    temp1.value += 1.0 * SQRT_SCALAR  # this doesn't seem to do much heh

    x_or_temp5.value = x
    x_or_temp5.value *= temp1
    x_or_temp5.value *= temp1

    temp2.value = x_or_temp5
    temp2.value /= 537752656.0
    temp2.value += 880298.0 * SQRT_SCALAR**2

    temp3.value = x_or_temp5
    temp3.value /= temp2
    temp3.value /= SQRT_INV_SCALAR**2  # can maybe take this line out somehow
    temp3.value += temp2

    temp2.value = x_or_temp5
    temp2.value /= temp3
    temp3.value *= 0.25 * SQRT_INV_SCALAR**2
    temp3.value += temp2

    temp4.value = x_or_temp5
    temp4.value /= temp3
    temp3.value /= SQRT_INV_SCALAR**2  # can maybe take this line out somehow
    temp4.value += temp3

    temp2.value = x_or_temp5
    temp2.value /= temp4
    temp4.value *= 0.25 * SQRT_INV_SCALAR
    temp2.value /= SQRT_INV_SCALAR  # can maybe take this line out somehow
    temp4.value += temp2

    assign_to.value = x_or_temp5
    assign_to.value /= temp4
    assign_to.value += temp4

    x_or_temp5.value /= assign_to
    assign_to.value /= 4.0
    assign_to.value += x_or_temp5

    assign_to.value += 1.0 * SQRT_SCALAR
    assign_to.value /= temp1


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
    temp1 = PlayerStat('temp1').as_double().without_automatic_unset()
    if not can_modify_x:
        x_or_temp2 = PlayerStat('temp2').as_double().without_automatic_unset()
    else:
        assert isinstance(x, Editable)
        x_or_temp2 = x.as_double()
        if isinstance(x_or_temp2, BaseStat):
            x_or_temp2 = x_or_temp2.without_automatic_unset()
    original_x = (
        PlayerStat('temp2' if can_modify_x else 'temp3')
        .as_double()
        .without_automatic_unset()
    )

    if certain_x_in_range != 90:
        if certain_x_in_range != 180:
            original_x.value = x % 360.0
            x_or_temp2.value = original_x + 90.0
            x_or_temp2.value = x_or_temp2 % 180.0 - 90.0
        else:
            with IfAnd(x >= 0.0):
                original_x.value = x
            with Else:
                original_x.value = x + 360.0
            x_or_temp2.value = original_x + 90.0
            with IfAnd(x_or_temp2 >= 180.0):
                x_or_temp2.value -= 180.0
            with IfAnd(x_or_temp2 >= 180.0):
                x_or_temp2.value -= 270.0
            with Else:
                x_or_temp2.value -= 90.0
    else:
        x_or_temp2.value = x

    assign_to_sin.value = x_or_temp2
    x_or_temp2.value *= x_or_temp2
    temp1.value = 32400.0
    temp1.value += x_or_temp2
    if cos_sign == 1:
        assign_to_cos.value = 32400.0
    else:
        assign_to_cos.value = -32400.0
    x_or_temp2.value *= 4.0
    if cos_sign == 1:
        assign_to_cos.value -= x_or_temp2
    else:
        assign_to_cos.value += x_or_temp2
    assign_to_cos.value /= temp1.value
    x_or_temp2.value *= assign_to_sin
    x_or_temp2.value /= 5508000.0

    if sin_sign == 1:
        assign_to_sin.value *= 0.017
        assign_to_sin.value -= x_or_temp2
    else:
        assign_to_sin.value *= -0.017
        assign_to_sin.value += x_or_temp2

    if certain_x_in_range != 90:
        with IfAnd(
            original_x >= 90.0,
            original_x < 270.0,
        ):
            assign_to_sin.value *= -1
            assign_to_cos.value *= -1
