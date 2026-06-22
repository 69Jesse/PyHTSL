from ..actions.conditional.statements import IfAll, IfAny
from ..checkable import Checkable
from ..stats.player_stat import PlayerStat
from ..stats.stat import Stat

__all__ = ('format_time_string',)


def format_time_string(
    raw_seconds: Checkable | int,
    *,
    output: Stat,
    separator: str = '',
) -> None:
    """Render a duration in seconds into ``output`` as e.g. ``1h12m`` (or
    ``1h 12m`` with ``separator=' '``). Seconds are dropped once days are
    present. ``separator`` goes between unit groups only — no leading or
    trailing separator."""
    # Explicit ops on named scratch stats only, so no anonymous optimizer
    # temporaries (which also live in the tmp<number> namespace) are created.
    # The two string scratch stats use short names so that concatenating two of
    # their placeholders (plus a separator) stays under the 32-char set limit.
    seconds = PlayerStat('tmp0').as_long().without_auto_unset()
    days = PlayerStat('tmp1').as_long().without_auto_unset()
    hours = PlayerStat('tmp2').as_long().without_auto_unset()
    minutes = PlayerStat('tmp3').as_long().without_auto_unset()
    scratch = PlayerStat('tmp4').as_long().without_auto_unset()
    show = PlayerStat('tmp5').as_long().without_auto_unset()
    has_content = PlayerStat('tmp6').as_long().without_auto_unset()
    buffer = PlayerStat('s0').as_string().without_auto_unset()
    piece = PlayerStat('s1').as_string().without_auto_unset()

    seconds.value = raw_seconds
    with IfAll(seconds < 0):
        seconds.value = 0

    def split(into: PlayerStat, divisor: int) -> None:
        into.value = seconds
        into.value //= divisor
        scratch.value = into
        scratch.value *= divisor
        seconds.value -= scratch

    split(days, 86400)
    split(hours, 3600)
    split(minutes, 60)

    buffer.value = ''
    has_content.value = 0

    # Largest unit first, appended left-to-right.
    units = (
        (days, 'd', (days,)),
        (hours, 'h', (hours, days)),
        (minutes, 'm', (minutes, hours, days)),
        (seconds, 's', None),  # seconds show only when there are no days
    )
    for stat, label, show_when in units:
        piece.value = stat.into_inside_string(include_fallback_value=True)

        show.value = 0
        if show_when is None:
            with IfAll(days == 0):
                show.value = 1
        else:
            with IfAny(*(s > 0 for s in show_when)):
                show.value = 1

        with IfAll(show == 1, has_content == 1):
            buffer.value = f'{buffer}{separator}{piece}{label}'
        with IfAll(show == 1, has_content == 0):
            buffer.value = f'{buffer}{piece}{label}'
        with IfAll(show == 1):
            has_content.value = 1

    output.without_auto_unset().value = buffer
