import re

PLACEHOLDER_PARTS_REGEX: re.Pattern[str] = re.compile(r'%[^%]*%')


def get_placeholder_parts(value: str) -> list[str]:
    # TODO fix
    parts: list[str] = []
    last_index = 0

    for match in PLACEHOLDER_PARTS_REGEX.finditer(value):
        start, end = match.span()
        parts.append(value[last_index:start])
        parts.append(match.group())
        last_index = end

    parts.append(value[last_index:])

    return parts
