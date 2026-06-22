def get_placeholder_parts(value: str) -> list[str]:
    from ..checkable import Checkable

    spans: list[tuple[int, int]] = []
    for pattern, _ in Checkable.iter_pattern_factories():
        for match in pattern.finditer(value):
            spans.append(match.span())

    spans.sort()

    parts: list[str] = []
    last_index = 0
    for start, end in spans:
        if start < last_index:
            continue
        parts.append(value[last_index:start])
        parts.append(value[start:end])
        last_index = end

    parts.append(value[last_index:])

    return parts
