from enum import Enum, auto


__all__ = (
    'LineType',
)


class LineType(Enum):
    player_stat_change = auto()
    global_stat_change = auto()
    team_stat_change = auto()
    misc_stat_change = auto()
    if_and_enter = auto()
    if_or_enter = auto()
    if_exit = auto()
    else_enter = auto()
    else_exit = auto()
    trigger_function = auto()
    exit_function = auto()
    cancel_event = auto()
    miscellaneous = auto()
    goto = auto()
    comment = auto()
    goto_move_to_end = auto()
