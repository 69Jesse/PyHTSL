from ...editable import Editable

__all__ = ('round_double',)


def round_double(
    x: Editable,
    decimals: int,
) -> None:
    x = x.as_double()

    factor = 10**decimals
    x.value *= factor
    x.value += 0.5

    x.cast_to_long()
    x.cast_to_double()

    x.value /= factor
