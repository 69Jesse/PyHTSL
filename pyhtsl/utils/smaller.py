import re


__all__ = (
    'remove_formatting',
    'get_placeholder_parts',
)


REMOVE_FORMATTING_REGEX = re.compile(r'&[0-9a-fk-or]')


def remove_formatting(value: str) -> str:
    return REMOVE_FORMATTING_REGEX.sub('', value)


PLACEHOLDER_PARTS_REGEX = re.compile(r'%[^%]*%')


def get_placeholder_parts(value: str) -> list[str]:
    parts: list[str] = []
    last_index = 0

    for match in PLACEHOLDER_PARTS_REGEX.finditer(value):
        start, end = match.span()
        parts.append(value[last_index:start])
        parts.append(match.group())
        last_index = end

    parts.append(value[last_index:])

    return parts
