from ..actions.conditional.statements import IfAll, IfAny
from ..checkable import Checkable
from ..stats.player_stat import PlayerStat
from ..stats.stat import Stat
from ..stats.temporary_stat import TemporaryStat

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
    seconds = TemporaryStat().as_long()
    days = TemporaryStat().as_long()
    hours = TemporaryStat().as_long()
    minutes = TemporaryStat().as_long()
    scratch = TemporaryStat().as_long()
    buffer = PlayerStat('s0').as_string().without_auto_unset()
    piece = PlayerStat('s1').as_string().without_auto_unset()

    seconds.value = raw_seconds
    with IfAll(seconds < 0):
        seconds.value = 0

    def split(into: TemporaryStat, divisor: int) -> None:
        into.value = seconds
        into.value //= divisor
        scratch.value = into
        scratch.value *= divisor
        seconds.value -= scratch

    split(days, 86400)
    split(hours, 3600)
    split(minutes, 60)

    buffer.value = ''

    def piece_of(stat: TemporaryStat) -> None:
        piece.value = stat.into_inside_string(include_fallback_value=True)

    if not separator:
        with IfAll(days == 0):
            piece_of(seconds)
            buffer.value = f'{piece}s'
        with IfAny(minutes > 0, hours > 0, days > 0):
            piece_of(minutes)
            buffer.value = f'{piece}m{buffer}'
        with IfAny(hours > 0, days > 0):
            piece_of(hours)
            buffer.value = f'{piece}h{buffer}'
        with IfAll(days > 0):
            piece_of(days)
            buffer.value = f'{piece}d{buffer}'
    else:
        has_content = TemporaryStat().as_long()
        show = TemporaryStat().as_long()
        has_content.value = 0
        units = (
            (seconds, 's', None),  # seconds show only when there are no days
            (minutes, 'm', (minutes, hours, days)),
            (hours, 'h', (hours, days)),
            (days, 'd', (days,)),
        )
        for stat, label, show_when in units:
            piece_of(stat)
            show.value = 0
            if show_when is None:
                with IfAll(days == 0):
                    show.value = 1
            else:
                with IfAny(*(s > 0 for s in show_when)):
                    show.value = 1
            with IfAll(show == 1, has_content == 1):
                buffer.value = f'{piece}{label}{separator}{buffer}'
            with IfAll(show == 1, has_content == 0):
                buffer.value = f'{piece}{label}'
                has_content.value = 1

    output.without_auto_unset().value = buffer
