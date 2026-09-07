import numpy as np

from pyhtsw.execute.java_string import exceeds_java_length

__all__ = (
    'NumericHousingType',
    'HousingType',
    'VALUE_MAX_LENGTH',
    'CHAT_INPUT_MAX_LENGTH',
    'housing_type_as_rhs',
    'housing_type_from_string',
    'check_value_length',
    'check_chat_input_length',
)


NumericHousingType = int | float
HousingType = NumericHousingType | str

VALUE_MAX_LENGTH = 32
CHAT_INPUT_MAX_LENGTH = 256


def housing_type_as_rhs(value: HousingType) -> str:
    if isinstance(value, NumericHousingType):
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            formatted = np.format_float_positional(value, trim='-')
            if '.' not in formatted:
                formatted += '.0'
            return formatted
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'


def housing_type_from_string(value: str) -> HousingType:
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def check_value_length(text: str, *, field: str) -> str:
    """The cap applies only to a quoted value; a bare placeholder or number is
    accepted at any length (htsw `parseValue`, and Housing itself)."""
    if not (len(text) >= 2 and text.startswith('"') and text.endswith('"')):
        return text
    typed = text[1:-1].replace('\\"', '"')
    length = exceeds_java_length(typed, VALUE_MAX_LENGTH)
    if length is None:
        return text
    raise ValueError(
        f'{field} renders {length} characters, over the '
        f'{VALUE_MAX_LENGTH}-character limit Housing puts on a quoted value: {text}. '
        f'Shorten the stat name, drop the fallback with "with NoFallbackValues():", '
        f'or render it as a bare placeholder with "with NoTypeCasting():".',
    )


def check_chat_input_length(text: str, *, field: str) -> str:
    length = exceeds_java_length(text, CHAT_INPUT_MAX_LENGTH)
    if length is None:
        return text
    raise ValueError(
        f'{field} renders {length} characters, over the '
        f'{CHAT_INPUT_MAX_LENGTH}-character limit Housing puts on a chat input.',
    )
