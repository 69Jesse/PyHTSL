from .smaller import remove_formatting, get_placeholder_parts


__all__ = ('compute_best_layout',)


def get_width(i: int, j: int, lengths: list[int]) -> int:
    return (j - i) + sum(lengths[k] for k in range(i, j + 1))


def get_cost(i: int, j: int, max_length: int, lengths: list[int]) -> float:
    width = get_width(i, j, lengths)
    if width > max_length:
        return float('inf')
    return (max_length - width) ** 3


def compute_line_start_indexes(lengths: list[int], max_length: int) -> list[int]:
    n = len(lengths)
    # T[j] stores minimum cost for first j words
    min_cost_up_to = [float('inf')] * (n + 1)
    # P[j] stores the starting index of the last line for optimal solution
    line_start_indexes = [0] * (n + 1)
    min_cost_up_to[0] = 0

    # Compute T and P arrays
    for j in range(1, n + 1):
        for i in range(1, j + 1):
            width = get_width(i - 1, j - 1, lengths)
            if width > max_length:
                continue

            cost = get_cost(i - 1, j - 1, max_length, lengths)
            if min_cost_up_to[i - 1] + cost >= min_cost_up_to[j]:
                continue

            min_cost_up_to[j] = min_cost_up_to[i - 1] + cost
            line_start_indexes[j] = i - 1  # Store where this line should start

    return line_start_indexes


def get_formatting_codes(text: str) -> list[list[str]]:
    result: list[list[str]] = []
    active_codes: list[str] = []
    i = 0

    additive_codes = set('klmno')
    color_codes = set('0123456789abcdef')
    reset_codes = {'r'}

    while i < len(text):
        if text[i] == '&' and i + 1 < len(text):
            code = text[i + 1]

            if code in color_codes:
                # Reset, then reapply this color (even if it's the same as previous)
                count = active_codes.count(code)
                active_codes = [code for _ in range(count + 1)]
                i += 2
                continue

            elif code in additive_codes:
                active_codes.append(code)
                i += 2
                continue

            elif code in reset_codes:
                active_codes = []
                i += 2
                continue

        if text[i] == '\n':
            active_codes = []

        result.append(active_codes.copy())
        i += 1

    return result


def add_formatting_codes(unformatted_text: str, formatting: list[list[str]]) -> str:
    result = []
    prev_codes: list[str] = []

    for ch, codes in zip(unformatted_text, formatting):
        if ch == '\n':
            result.append(ch)
            prev_codes = []
            continue

        if codes != prev_codes:
            # Compute minimal change needed: insert only what was added
            if not codes:
                result.append('&r')
            else:
                # If codes changed, insert exactly the new codes (preserve duplication)
                new_codes = []
                for i in range(len(codes)):
                    if i < len(prev_codes) and codes[i] == prev_codes[i]:
                        continue
                    new_codes.append(codes[i])
                result.extend('&' + c for c in new_codes)

        result.append(ch)
        prev_codes = codes

    return ''.join(result)


def compute_best_layout_raw(
    words: list[str],
    max_length: int,
    lengths: list[int] | None = None,
) -> str:
    lengths = lengths or list(map(len, words))

    line_start_indexes = compute_line_start_indexes(lengths, max_length)

    # Reconstruct the solution
    lines = []
    j = len(lengths)
    while j > 0:
        i = line_start_indexes[j]
        lines.insert(0, words[i:j])
        j = i

    return '\n'.join(map(' '.join, lines))


def compute_best_layout(
    text: str,
    *,
    max_length: int = 40,
    placeholder_length: int = 4,
) -> str:
    unformatted_text = remove_formatting(text)
    assert (
        '\n' not in text
        and '  ' not in unformatted_text
        and not unformatted_text.startswith(' ')
        and not unformatted_text.endswith(' ')
    )

    parts = get_placeholder_parts(unformatted_text)
    words: list[str] = []
    lengths: list[int] = []
    lengths_increments: dict[int, int] = {}
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part == '':
                continue
            split = part.split(' ')
            first = split.pop(0)
            if first != '' and i > 0:
                words[-1] = words[-1] + first
                lengths[-1] += len(first)
                if not split and i < len(parts) - 1:
                    words[-1] = words[-1] + parts[i + 1]
                    lengths[-1] += placeholder_length
                    parts[i + 1] = ''
                    continue
            elif first != '':
                split.insert(0, first)

            last = split.pop(-1)
            if last != '' and i < len(parts) - 1:
                parts[i + 1] = last + parts[i + 1]
                lengths_increments[i + 1] = len(last)
            elif last != '':
                split.append(last)

            for word in split:
                assert word != ''
                words.append(word)
                lengths.append(len(word))

        else:
            if not part:
                continue
            words.append(part)
            lengths.append(placeholder_length + lengths_increments.get(i, 0))

    codes: list[list[str]] = get_formatting_codes(text)
    layout = compute_best_layout_raw(
        words,
        max_length=max_length,
        lengths=lengths,
    )
    assert len(layout) == len(codes)
    return add_formatting_codes(layout, codes)
