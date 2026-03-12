import re


def into_slug(text: str, *, symbol: str = '_') -> str:
    text = re.sub(r'[^a-z0-9]+', symbol, text.lower()).strip(symbol)
    while (symbol * 2) in text:
        text = text.replace(f'{symbol}{symbol}', symbol)
    return text
