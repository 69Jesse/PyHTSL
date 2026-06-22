from ..actions.conditional.statements import IfAll
from ..checkable import Checkable
from ..editable import Editable
from ..stats.player_stat import PlayerStat

__all__ = ('set_ordinal_inline',)


def set_ordinal_inline(
    checking_stat: Checkable,
    output_stat: Editable,
) -> None:
    """Set ``output_stat`` to the English ordinal suffix ('st'/'nd'/'rd'/'th')
    for ``checking_stat``."""
    # Explicit modulo via named scratch stats only — using ``.remainder`` would
    # spawn anonymous tmp<number> temporaries that the optimizer could merge
    # with these result stats.
    last_two_digits = PlayerStat('tmp0').as_long().without_auto_unset()
    last_digit = PlayerStat('tmp1').as_long().without_auto_unset()
    scratch = PlayerStat('tmp2').as_long().without_auto_unset()

    def assign_modulo(into: PlayerStat, value: Checkable, divisor: int) -> None:
        into.value = value
        scratch.value = into
        scratch.value //= divisor
        scratch.value *= divisor
        into.value -= scratch

    assign_modulo(last_two_digits, checking_stat, 100)
    assign_modulo(last_digit, last_two_digits, 10)

    output_stat.value = 'th'
    reversed_conditions = [
        ~(last_two_digits == 11),
        ~(last_two_digits == 12),
        ~(last_two_digits == 13),
    ]  # 11/12/13 stay 'th'

    condition = last_digit == 1
    with IfAll(*reversed_conditions, condition):
        output_stat.value = 'st'
    reversed_conditions.append(~condition)

    condition = last_digit == 2
    with IfAll(*reversed_conditions, condition):
        output_stat.value = 'nd'
    reversed_conditions.append(~condition)

    condition = last_digit == 3
    with IfAll(*reversed_conditions, condition):
        output_stat.value = 'rd'
    reversed_conditions.append(~condition)

    # else: 'th' (already set)
