from ..writer import WRITER


__all__ = (
    'display_action_bar',
)


def display_action_bar(
    text: str,
) -> None:
    WRITER.write(f'actionBar "{text}"')
