from ..editable import Editable
from ..expression.binary_expression import SET_STRING_MAX_LENGTH
from ..utils.placeholders import get_placeholder_parts

__all__ = ('set_string',)


def _atomize(value: str) -> list[str]:
    """Split value into indivisible atoms: each character of literal text and
    each placeholder source string.
    """
    parts = get_placeholder_parts(value)
    atoms: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            atoms.extend(part)
        else:
            atoms.append(part)
    return atoms


def _has_placeholders(value: str) -> bool:
    parts = get_placeholder_parts(value)
    return any(parts[i] for i in range(1, len(parts), 2))


def set_string(stat: Editable, value: str) -> None:
    if len(value) <= SET_STRING_MAX_LENGTH:
        stat.value = value
        return

    if not _has_placeholders(value):
        raise ValueError(
            f'set_string: value of {len(value)} chars has no '
            f'placeholders to shrink it under the {SET_STRING_MAX_LENGTH}-char limit'
        )

    self_ref = str(stat)
    self_ref_len = len(self_ref)
    if self_ref_len >= SET_STRING_MAX_LENGTH:
        raise ValueError(
            f'set_string: stat self-reference {self_ref!r} is {self_ref_len} '
            f'chars; no room for content within the '
            f'{SET_STRING_MAX_LENGTH}-char limit'
        )

    budget_continuation = SET_STRING_MAX_LENGTH - self_ref_len
    atoms = _atomize(value)

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def budget() -> int:
        return SET_STRING_MAX_LENGTH if not chunks else budget_continuation

    for atom in atoms:
        atom_len = len(atom)
        if current_len + atom_len > budget():
            if not current:
                raise ValueError(
                    f'set_string: atom {atom!r} of {atom_len} chars exceeds '
                    f'chunk budget of {budget()} chars'
                )
            chunks.append(''.join(current))
            current = []
            current_len = 0
            if atom_len > budget():
                raise ValueError(
                    f'set_string: atom {atom!r} of {atom_len} chars exceeds '
                    f'chunk budget of {budget()} chars'
                )
        current.append(atom)
        current_len += atom_len

    if current:
        chunks.append(''.join(current))

    stat.value = chunks[0]
    for chunk in chunks[1:]:
        stat.value = self_ref + chunk
