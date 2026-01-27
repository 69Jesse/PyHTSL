from .smaller import get_placeholder_parts
from ..editable import Editable
from ..stats.player_stat import PlayerStat


__all__ = ('set_string',)


def get_set_string_parts(value: str) -> list[str]:
    raw_parts = get_placeholder_parts(value)
    parts: list[str] = []
    for i, part in enumerate(raw_parts):
        if i % 2 == 0:
            parts.extend(list(part))
        else:
            parts.append(part)

    previous_was_space = False
    for i in range(len(parts) - 1, -1, -1):
        if previous_was_space:
            parts[i] = parts[i] + parts[i + 1]
            parts.pop(i + 1)
        if parts[i] == ' ':
            previous_was_space = True
            parts.pop(i)
            if i >= len(parts):
                continue
            parts[i] = ' ' + parts[i]
        else:
            previous_was_space = False

    return parts


def set_string(stat: Editable, value: str) -> None:
    parts = get_set_string_parts(value)
    assert len(parts) >= 1

    temp_stat = PlayerStat('t').as_string()
    used_temp_stat = False

    stat_str_length = len(str(stat))

    index = 0
    while index < len(parts):
        is_first_time = index == 0
        part = parts[index]
        index += 1
        while index < len(parts) and len(part) + len(parts[index]) <= 32:
            part = part + parts[index]
            index += 1
        assert len(part) <= 32
        if not is_first_time:
            if len(part) + stat_str_length <= 32:
                part = f'{stat}{part}'
            else:
                temp_stat.value = part
                used_temp_stat = True
                part = f'{stat}{temp_stat}'
        stat.value = part
    if used_temp_stat:
        temp_stat.unset()
