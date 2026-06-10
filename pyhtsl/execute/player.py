from typing import TYPE_CHECKING, Literal, overload

from ..checkable import Checkable
from ..expression.housing_type import HousingType
from .backend_type import BackendType

if TYPE_CHECKING:
    from .context import ExecutionContext

__all__ = ('ExecutionPlayer',)


class ExecutionPlayer:
    """A simulated player inside an `ExecutionContext`.

    Player-scoped state (`var` / `%player.…%`) lives in `mapping`; everything
    else (`globalvar`, …) lives on the context and is shared. Every read/write
    method just forwards to the owning context bound to `self`, so there is a
    single source of truth for the get/put/substitute logic.
    """

    name: str | None
    context: 'ExecutionContext | None'
    mapping: dict[tuple[object, ...], BackendType]
    functions_on_cooldown_for_ticks: dict[str, int]

    def __init__(self, name: str | None = None) -> None:
        self.name = name
        self.context = None
        self.mapping = {}
        self.functions_on_cooldown_for_ticks = {}

    def _context(self) -> 'ExecutionContext':
        if self.context is None:
            raise RuntimeError(
                'This ExecutionPlayer is not attached to an ExecutionContext yet. '
                'Pass it via ExecutionContext(players=[...]) or context.add_player(...).'
            )
        return self.context

    def put(
        self,
        key: Checkable,
        value: HousingType | BackendType,
        *,
        ignore_warning: bool = False,
    ) -> None:
        self._context().put(key, value, ignore_warning=ignore_warning, player=self)

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['regular'] = ...,
    ) -> HousingType: ...

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['backend'],
    ) -> BackendType: ...

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['string'],
    ) -> str: ...

    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['regular', 'backend', 'string'] = 'regular',
    ) -> HousingType | BackendType | str:
        return self._context().get(key, cast=cast, output=output, player=self)

    def get_raw(
        self,
        key: Checkable,
        *,
        default: HousingType | None = None,
    ) -> HousingType:
        return self._context().get_raw(key, default=default, player=self)

    def pop(self, key: Checkable) -> None:
        self._context().pop(key, player=self)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name!r})'
