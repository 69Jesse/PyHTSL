import numpy as np
from abc import ABC, abstractmethod
import re

from typing import Any, Self


class NBT[T](ABC):
    value: T

    def __init__(self, value: T) -> None:
        self.value = value

    @abstractmethod
    def to_snbt(self) -> str:
        """
        Convert the NBT object to a string in SNBT format.
        """
        raise NotImplementedError

    @abstractmethod
    def to_object(self) -> Any:
        """
        Convert the NBT object to a Python object.
        """
        raise NotImplementedError

    @classmethod
    def from_snbt(cls, s: str) -> 'NBT':
        """
        Load the NBT object from a string in SNBT format.
        Raises an exception if the string is not valid SNBT.
        """
        nbt, offset = cls._parse_snbt(s)
        if offset == len(s):
            return nbt
        raise ValueError(
            f'Invalid SNBT format: {repr(s)} ({len(s) - offset} characters left)'
        )

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        """
        Parse the SNBT string and try to extract the NBT object.
        Returns a tuple of the NBT object and the amount of characters consumed.
        Raises an exception if the string is not valid SNBT.
        """
        for subclass in cls.__subclasses__():
            if subclass is NBT:
                continue
            try:
                return subclass._parse_snbt(s)
            except ValueError:
                continue
        raise ValueError(f'Invalid SNBT format: {repr(s)}')

    @classmethod
    def from_object(cls, obj: Any) -> 'NBT':
        """
        Load the NBT object from a Python object.
        Raises an exception if the object is not valid.
        """
        if isinstance(obj, NBT):
            return obj
        for subclass in cls.__subclasses__():
            if subclass is NBT:
                continue
            try:
                return subclass.from_object(obj)
            except Exception:
                continue
        raise ValueError(f'Invalid object for NBT: {repr(obj)}')

    def __str__(self) -> str:
        return self.to_snbt()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.value)}>'


class NBTByte(NBT[int]):
    def __init__(self, value: int = 0) -> None:
        if not isinstance(value, int):
            raise TypeError('Value must be an integer')
        if not -128 <= value <= 127:
            raise ValueError('Value must be between -128 and 127')
        super().__init__(value)

    def to_snbt(self) -> str:
        return f'{self.to_object()}b'

    def to_object(self) -> int:
        return self.value

    BYTE_REGEX: re.Pattern[str] = re.compile(r'^-?\d{1,3}[bB]', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.BYTE_REGEX.match(s)
        if not match:
            raise ValueError('Invalid SNBT format for NBTByte')
        value = int(match.group(0)[:-1])
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTByte':
        if isinstance(obj, NBTByte):
            return obj
        return cls(obj)


class NBTBoolean(NBTByte):
    def __init__(self, value: int | bool = False) -> None:
        if isinstance(value, int):
            if value not in (0, 1):
                raise ValueError('Value must be 0 or 1 for NBTBoolean')
            value = bool(value)
        if not isinstance(value, bool):
            raise TypeError('Value must be a boolean')
        super().__init__(value)

    def to_snbt(self) -> str:
        return 'true' if self.value else 'false'

    def to_object(self) -> bool:
        return self.value  # type: ignore

    BOOLEAN_REGEX: re.Pattern[str] = re.compile(r'^(true|false|[10][bB])', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.BOOLEAN_REGEX.match(s)
        if not match:
            raise ValueError('Invalid SNBT format for NBTBoolean')
        value = match.group(0)
        if value in ('true', '1b', '1B'):
            return cls(True), match.end(0)
        elif value in ('false', '0b', '0B'):
            return cls(False), match.end(0)
        raise ValueError('Invalid SNBT format for NBTBoolean')

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTBoolean':
        if isinstance(obj, NBTBoolean):
            return obj
        return cls(obj)


class NBTShort(NBT[int]):
    def __init__(self, value: int = 0) -> None:
        if not isinstance(value, int):
            raise TypeError('Value must be an integer')
        if not -32768 <= value <= 32767:
            raise ValueError('Value must be between -32768 and 32767')
        super().__init__(value)

    def to_snbt(self) -> str:
        return f'{self.to_object()}s'

    def to_object(self) -> int:
        return self.value

    SHORT_REGEX: re.Pattern[str] = re.compile(r'^-?\d{1,5}[sS]', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.SHORT_REGEX.match(s)
        if not match:
            raise ValueError('Invalid SNBT format for NBTShort')
        value = int(match.group(0)[:-1])
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTShort':
        if isinstance(obj, NBTShort):
            return obj
        return cls(obj)


class NBTInt(NBT[int]):
    def __init__(self, value: int = 0) -> None:
        if not isinstance(value, int):
            raise TypeError('Value must be an integer')
        if not -2147483648 <= value <= 2147483647:
            raise ValueError('Value must be between -2147483648 and 2147483647')
        super().__init__(value)

    def to_snbt(self) -> str:
        return str(self.to_object())

    def to_object(self) -> int:
        return self.value

    INT_REGEX: re.Pattern[str] = re.compile(r'^-?\d{1,10}', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.INT_REGEX.match(s)
        if not match:
            raise ValueError('Invalid SNBT format for NBTInt')
        value = int(match.group(0))
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTInt':
        if isinstance(obj, NBTInt):
            return obj
        return cls(obj)


class NBTLong(NBT[int]):
    def __init__(self, value: int = 0) -> None:
        if not isinstance(value, int):
            raise TypeError('Value must be an integer')
        if not -9223372036854775808 <= value <= 9223372036854775807:
            raise ValueError(
                'Value must be between -9223372036854775808 and 9223372036854775807'
            )
        super().__init__(value)

    def to_snbt(self) -> str:
        return f'{self.to_object()}l'

    def to_object(self) -> int:
        return self.value

    LONG_REGEX: re.Pattern[str] = re.compile(r'^-?\d{1,19}[lL]', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.LONG_REGEX.match(s)
        if not match:
            raise ValueError('Invalid SNBT format for NBTLong')
        value = int(match.group(0)[:-1])
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTLong':
        if isinstance(obj, NBTLong):
            return obj
        return cls(obj)


class NBTFloat(NBT[float]):
    def __init__(self, value: float = 0.0) -> None:
        if not isinstance(value, float):
            raise TypeError('Value must be a float')
        super().__init__(value)

    def to_snbt(self) -> str:
        formatted = np.format_float_positional(self.to_object(), trim='-')
        if '.' not in formatted:
            formatted += '.0'
        return f'{formatted}f'

    def to_object(self) -> float:
        return self.value

    FLOAT_REGEX: re.Pattern[str] = re.compile(r'^-?\d+(\.\d+)?[fF]', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.FLOAT_REGEX.match(s)
        if not match:
            raise ValueError('Invalid SNBT format for NBTFloat')
        value = float(match.group(0)[:-1])
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTFloat':
        if isinstance(obj, NBTFloat):
            return obj
        return cls(obj)


class NBTDouble(NBT[float]):
    def __init__(self, value: float = 0.0) -> None:
        if not isinstance(value, float):
            raise TypeError('Value must be a float')
        super().__init__(value)

    def to_snbt(self) -> str:
        formatted = np.format_float_positional(self.to_object(), trim='-')
        if '.' not in formatted:
            formatted += '.0'
        return formatted

    def to_object(self) -> float:
        return self.value

    DOUBLE_REGEX: re.Pattern[str] = re.compile(r'^-?\d+(\.\d+)?[dD]?', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.DOUBLE_REGEX.match(s)
        if not match:
            raise ValueError('Invalid SNBT format for NBTDouble')
        raw = match.group(0)
        if raw.endswith(('d', 'D')):
            raw = raw[:-1]
        value = float(raw)
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTDouble':
        if isinstance(obj, NBTDouble):
            return obj
        return cls(obj)


class NBTString(NBT[str]):
    def __init__(self, value: str = '') -> None:
        if not isinstance(value, str):
            raise TypeError('Value must be a string')
        super().__init__(value)

    def to_snbt(self) -> str:
        return f'"{self.to_object().replace('"', '\\"')}"'

    def to_object(self) -> str:
        return self.value

    QUOTES: tuple[tuple[str, str], tuple[str, str]] = (('"', '"'), ("'", "'"))

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        for start, end in cls.QUOTES:
            if not s.startswith(start):
                continue
            offset = len(start)
            while offset < len(s) and (
                s[offset] != end or (offset > 0 and s[offset - 1] == '\\')
            ):
                offset += 1
            if offset >= len(s) or s[offset] != end:
                raise ValueError('Invalid SNBT format for NBTString')
            value = s[1:offset]
            return cls(value), offset + 1
        raise ValueError('Invalid SNBT format for NBTString')

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTString':
        if isinstance(obj, NBTString):
            return obj
        return cls(obj)


class NBTList[T: NBT](NBT[list[T]]):
    def __init__(self, value: list[T] | None = None) -> None:
        if value is None:
            value = []
        if not isinstance(value, list):
            raise TypeError('Value must be a list')
        if len(value) > 0:
            if not isinstance(value[0], NBT):
                raise ValueError('All items must be NBT instances')
            for i in range(1, len(value)):
                if not isinstance(value[i], value[0].__class__):
                    raise ValueError(
                        f'All items must be instances of {value[0].__class__.__name__}'
                    )
        super().__init__(value)

    def to_snbt(self) -> str:
        return f'[{",".join(item.to_snbt() for item in self.value)}]'

    def to_object(self) -> list[T]:
        return [item.to_object() for item in self.value]

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        if not s.startswith('['):
            raise ValueError('Invalid SNBT format for NBTList')
        offset = 1
        items: list[T] = []
        while offset < len(s) and s[offset] != ']':
            rest = s[offset:]
            maybe_prefix = f'{len(items)}:'
            if rest.startswith(maybe_prefix):
                rest = rest[len(maybe_prefix) :]
                offset += len(maybe_prefix)

            item, length = NBT._parse_snbt(rest)
            items.append(item)  # type: ignore
            offset += length

            if s[offset] == ']':
                break
            if s[offset] != ',':
                raise ValueError('Invalid SNBT format for NBTList')
            offset += 1
        return cls(items), offset + 1

    @classmethod
    def from_object(cls, obj: list[T]) -> 'NBTList':
        if isinstance(obj, NBTList):
            return obj
        return cls(obj)

    def __len__(self) -> int:
        return len(self.value)

    def is_empty(self) -> bool:
        return len(self.value) == 0

    def __getitem__(self, index: int) -> T:
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        return self.value[index]

    def __setitem__(self, index: int, value: T) -> None:
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        if len(self.value) > 0:
            if not isinstance(value, self.value[0].__class__):
                raise ValueError(
                    f'Value must be an instance of {self.value[0].__class__.__name__}'
                )
        self.value[index] = value

    def append(self, value: T) -> Self:
        if len(self.value) > 0:
            if not isinstance(value, self.value[0].__class__):
                raise ValueError(
                    f'Value must be an instance of {self.value[0].__class__.__name__}'
                )
        self.value.append(value)
        return self


class NBTCompound[V: NBT](NBT[dict[str, V]]):
    def __init__(self, value: dict[str, V] | None = None) -> None:
        if value is None:
            value = {}
        if not isinstance(value, dict):
            raise TypeError('Value must be a dictionary')
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError('Keys must be strings')
            if not isinstance(item, NBT):
                raise ValueError('All items must be NBT instances')
        super().__init__(value)

    def to_snbt(self) -> str:
        def format_key(key: str) -> str:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                return f'"{key.replace('"', '\\"')}"'
            return key

        return (
            '{'
            + ','.join(
                f'{format_key(key)}:{item.to_snbt()}'
                for key, item in self.value.items()
            )
            + '}'
        )

    def to_object(self) -> dict[str, Any]:
        return {key: item.to_object() for key, item in self.value.items()}

    KEY_REGEX: re.Pattern[str] = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        if not s.startswith('{'):
            raise ValueError('Invalid SNBT format for NBTCompound')
        offset = 1
        compound: dict[str, V] = {}
        while offset < len(s) and s[offset] != '}':
            key_start = offset
            while offset < len(s) and s[offset] not in (':', ',', '}'):
                offset += 1
            if offset >= len(s) or s[offset] != ':':
                raise ValueError('Invalid SNBT format for NBTCompound')
            key = s[key_start:offset].strip()
            if not cls.KEY_REGEX.match(key):
                try:
                    key = NBTString._parse_snbt(s[key_start:offset])[0].to_object()
                except Exception:
                    raise ValueError(f'Invalid key format in NBTCompound: {repr(key)}')

            if key in compound:
                raise ValueError(f'Duplicate key found in NBTCompound: {repr(key)}')

            offset += 1
            value, length = NBT._parse_snbt(s[offset:])
            compound[key] = value  # type: ignore
            offset += length

            if s[offset] == '}':
                break
            if s[offset] != ',':
                raise ValueError('Invalid SNBT format for NBTCompound')
            offset += 1

        return cls(compound), offset + 1

    @classmethod
    def from_object(cls, obj: dict[str, Any]) -> 'NBTCompound[V]':
        if isinstance(obj, NBTCompound):
            return obj
        compound: dict[str, V] = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError('Keys must be strings')
            compound[key] = NBT.from_object(value)  # type: ignore
        return cls(compound)

    def __len__(self) -> int:
        return len(self.value)

    def is_empty(self) -> bool:
        return len(self.value) == 0

    def get(self, key: str, default: V | None = None) -> V | None:
        if not isinstance(key, str):
            raise TypeError('Key must be a string')
        return self.value.get(key, default)

    def __getitem__(self, key: str) -> V:
        if not isinstance(key, str):
            raise TypeError('Key must be a string')
        if key not in self.value:
            raise KeyError(f'Key {repr(key)} not found in NBTCompound')
        return self.value[key]

    def put(self, key: str, value: V) -> Self:
        if not isinstance(key, str):
            raise TypeError('Key must be a string')
        if not isinstance(value, NBT):
            raise ValueError('Value must be an NBT instance')
        self.value[key] = value
        return self


class NBTGenericArray[IT: NBT, OT](NBT[list[IT]]):
    item_type: type[IT]
    id_character: str

    def __init_subclass__(cls, item_type: type[IT], id_character: str) -> None:
        super().__init_subclass__()
        cls.item_type = item_type
        assert len(id_character) == 1, 'id_character must be a single character'
        cls.id_character = id_character

    def __init__(self, value: list[IT] | None = None) -> None:
        if value is None:
            value = []
        if not isinstance(value, list):
            raise TypeError('Value must be a list')
        for item in value:
            if not isinstance(item, self.item_type):
                raise ValueError(
                    f'All items must be {self.item_type.__name__} instances'
                )
        super().__init__(value)

    def to_snbt(self) -> str:
        return (
            f'[{self.id_character};{",".join(item.to_snbt() for item in self.value)}]'
        )

    def to_object(self) -> list[OT]:
        return [item.to_object() for item in self.value]

    @classmethod
    def parse_nbt(cls, s: str) -> tuple[Self, int]:
        assert len(cls.id_character) == 1
        if not s.startswith(f'[{cls.id_character};'):
            raise ValueError(
                f'Invalid SNBT format for NBT{cls.id_character.upper()}Array'
            )
        offset = 3
        items: list[IT] = []
        while offset < len(s) and s[offset] != ']':
            item, length = cls.item_type._parse_snbt(s[offset:])
            items.append(item)
            offset += length
            if s[offset] == ']':
                break
            if s[offset] != ',':
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            offset += 1
        return cls(items), offset + 1

    @classmethod
    def from_object(cls, obj: Any) -> Self:
        if isinstance(obj, cls):
            return obj
        if not isinstance(obj, list):
            raise TypeError('Value must be a list')
        return cls([cls.item_type.from_object(item) for item in obj])  # type: ignore

    def __len__(self) -> int:
        return len(self.value)

    def is_empty(self) -> bool:
        return len(self.value) == 0

    def __getitem__(self, index: int) -> IT:
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        return self.value[index]

    def __setitem__(self, index: int, value: IT) -> None:
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        if not isinstance(value, self.item_type):
            raise ValueError(f'Value must be an instance of {self.item_type.__name__}')
        self.value[index] = value

    def append(self, value: IT) -> Self:
        if not isinstance(value, self.item_type):
            raise ValueError(f'Value must be an instance of {self.item_type.__name__}')
        self.value.append(value)
        return self


class NBTByteArray(NBTGenericArray[NBTByte, int], item_type=NBTByte, id_character='B'):
    pass


class NBTIntArray(NBTGenericArray[NBTInt, int], item_type=NBTInt, id_character='I'):
    pass


class NBTLongArray(NBTGenericArray[NBTLong, int], item_type=NBTLong, id_character='L'):
    pass
