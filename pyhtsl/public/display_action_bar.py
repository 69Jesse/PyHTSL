from ..write import write


__all__ = (
    'display_action_bar',
)


def display_action_bar(
    text: str,
) -> None:
    write(f'actionBar "{text}"')
