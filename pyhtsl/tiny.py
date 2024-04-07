from .write import write


def chat(
    line: str,
) -> None:
    write(f'chat "{line}"')
