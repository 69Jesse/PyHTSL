import re


def into_kebab(text: str, *, default: str = 'unnamed') -> str:
    text = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return text or default
