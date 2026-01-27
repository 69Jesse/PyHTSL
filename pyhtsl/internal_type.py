from enum import Enum


__all__ = ('InternalType',)


class InternalType(Enum):
    ANY = 0
    LONG = 1
    DOUBLE = 2
    STRING = 3
