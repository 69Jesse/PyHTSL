from ..editable import Editable
from ..expression.binary_expression import SET_STRING_MAX_LENGTH
from ..stats.player_stat import PlayerStat
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
    """Set ``stat`` to ``value`` (which may contain placeholders, including the
    stat's own) across as many ≤32-char assignments as needed. An oversized
    placeholder atom is offloaded into a short scratch stat first, then appended
    via its short reference, so long target names still fit the limit."""
    if len(value) <= SET_STRING_MAX_LENGTH:
        stat.value = value
        return

    if not _has_placeholders(value):
        raise ValueError(
            f'set_string: value of {len(value)} chars has no '
            f'placeholders to shrink it under the {SET_STRING_MAX_LENGTH}-char limit',
        )

    self_ref = str(stat)
    if len(self_ref) >= SET_STRING_MAX_LENGTH:
        raise ValueError(
            f'set_string: stat self-reference {self_ref!r} is {len(self_ref)} '
            f'chars; no room for content within the '
            f'{SET_STRING_MAX_LENGTH}-char limit',
        )

    scratch = PlayerStat('t').as_string()
    scratch_ref = str(scratch)
    continuation_budget = SET_STRING_MAX_LENGTH - len(self_ref)
    used_scratch = False

    atoms = _atomize(value)
    index = 0
    first = True
    while index < len(atoms):
        budget = SET_STRING_MAX_LENGTH if first else continuation_budget
        chunk = ''
        while index < len(atoms) and len(chunk) + len(atoms[index]) <= budget:
            chunk += atoms[index]
            index += 1

        if not chunk:
            atom = atoms[index]
            if len(atom) > SET_STRING_MAX_LENGTH:
                raise ValueError(
                    f'set_string: atom {atom!r} of {len(atom)} chars exceeds '
                    f'the {SET_STRING_MAX_LENGTH}-char limit',
                )
            if len(scratch_ref) > continuation_budget:
                raise ValueError(
                    f'set_string: target self-reference {self_ref!r} leaves no '
                    f'room to append content within the {SET_STRING_MAX_LENGTH}-char limit',
                )
            scratch.value = atom
            used_scratch = True
            index += 1
            chunk = scratch_ref

        if first:
            stat.value = chunk
            first = False
        else:
            stat.value = self_ref + chunk

    if used_scratch:
        scratch.unset()
