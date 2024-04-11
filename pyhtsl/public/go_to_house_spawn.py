from ..writer import WRITER


__all__ = (
    'go_to_house_spawn',
)


def go_to_house_spawn() -> None:
    WRITER.write('houseSpawn')
