from ..writer import WRITER


__all__ = (
    'full_heal',
)


def full_heal() -> None:
    WRITER.write('fullHeal')
