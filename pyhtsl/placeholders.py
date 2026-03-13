from abc import ABC, abstractmethod
from typing import final

from pyhtsl.editable import Editable

from .checkable import Checkable
from .execute.backend_type import BackendType
from .internal_type import InternalType

__all__ = (
    'PlaceholderCheckable',
    'PlaceholderEditable',
)


class PlaceholderCheckable(Checkable, ABC):
    as_string: str
    constant_internal_type: InternalType
    default_backend_value: BackendType

    def __init__(
        self,
        *,
        as_string: str,
        constant_internal_type: InternalType,
    ) -> None:
        super().__init__(internal_type=constant_internal_type)
        self.as_string = as_string
        self.constant_internal_type = constant_internal_type

    @abstractmethod
    def get_backend_value(self) -> BackendType:
        raise NotImplementedError

    @final
    def get_backend_fallback_value(self) -> BackendType | None:
        return super().get_backend_fallback_value() or self.get_backend_value()

    def into_string_lhs(self) -> str:
        return f'placeholder {self.inline_quoted(self.as_string)}'

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        return self.format_with_internal_type(
            self.as_string,
            include_internal_type=include_internal_type,
        )

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        return self.as_string

    def equals_raw(self, other: object) -> bool:
        return self is other

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.as_string}>'


class PlaceholderEditable(PlaceholderCheckable, Editable, ABC):
    assignment_lhs: str

    def __init__(
        self,
        *,
        assignment_lhs: str,
        as_string: str,
        constant_internal_type: InternalType,
    ) -> None:
        super().__init__(
            as_string=as_string,
            constant_internal_type=constant_internal_type,
        )
        self.assignment_lhs = assignment_lhs

    def into_string_lhs(self) -> str:
        return self.assignment_lhs
