from ..condition import PlaceholderValue
from .stat import Stat

from typing import final, Optional


@final
class ComparableStat(Stat, PlaceholderValue):
    full_placeholder: str
    edge_case_left_side: Optional[str]
    def __init__(
        self,
        name: str,
        full_placeholder: str,
        edge_case_left_side: Optional[str] = None,
    ) -> None:
        Stat.__init__(self, name)
        self.full_placeholder = full_placeholder
        self.edge_case_left_side = edge_case_left_side

    def get_prefix(self) -> str:
        raise NotImplementedError

    def get_placeholder_word(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.full_placeholder

    def __repr__(self) -> str:
        return self.name

    def operational_expression_left_side(self) -> str:
        if self.edge_case_left_side is not None:
            return self.edge_case_left_side
        return super().operational_expression_left_side()
