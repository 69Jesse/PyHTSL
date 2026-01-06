from enum import Enum, auto


class LineType(Enum):
    variable_change = auto()
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
    random_enter = auto()
    random_exit = auto()
    display_title = auto()
    pause_execution = auto()

    def is_if_enter(self) -> bool:
        return self is LineType.if_and_enter or self is LineType.if_or_enter
