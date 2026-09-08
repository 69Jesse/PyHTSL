from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyhtsw.base_object import BaseObject

__all__ = (
    'Missing',
    'MISSING',
    'clone_with',
    'build_clone_spec',
)


class Missing(Enum):
    # A single-member enum rather than a bare instance so `is MISSING` narrows,
    # and so the swap to PEP 661's typing.Sentinel is a drop-in.
    MISSING = 1

    def __repr__(self) -> str:
        return 'MISSING'


MISSING = Missing.MISSING


_BaseObject: type | None = None


def _base_object() -> type:
    global _BaseObject
    if _BaseObject is None:
        from pyhtsw.base_object import BaseObject

        _BaseObject = BaseObject
    return _BaseObject


def _copied(value: Any, base: type) -> Any:
    if isinstance(value, base):
        return value.cloned()
    if type(value) is list:
        return [v.cloned() if isinstance(v, base) else v for v in value]
    if type(value) is tuple:
        return tuple(v.cloned() if isinstance(v, base) else v for v in value)
    return value


def build_clone_spec(cls: type) -> None:
    """Derives the clone spec from `__init__` and caches it on the class. A
    class that declares `__clone_fields__` in its own body keeps that instead."""
    declared = cls.__dict__.get('__clone_fields__')
    if declared is not None:
        fields: tuple[str, ...] = tuple(declared)
        posonly = cls.__dict__.get('__clone_posonly__', 0)
    else:
        code = getattr(cls.__init__, '__code__', None)
        if code is None:
            fields = ()
            posonly = 0
        else:
            fields = code.co_varnames[: code.co_argcount + code.co_kwonlyargcount]
            posonly = code.co_posonlyargcount
            if fields and fields[0] == 'self':
                fields = fields[1:]
                posonly = max(0, posonly - 1)
    cls.__clone_fields__ = fields  # type: ignore[attr-defined]
    cls.__clone_posonly__ = posonly  # type: ignore[attr-defined]

    mapping: dict[str, str] = {}
    for base in reversed(cls.__mro__):
        mapping.update(base.__dict__.get('__clone_map__', {}))
    cls.__clone_map__ = mapping  # type: ignore[attr-defined]

    # Declarations are read only from `__clone_extra__` and the deduped result is
    # written to `__clone_carry__`: a name that is a *this* class's constructor
    # field may still need carrying on a subclass whose __init__ drops it, so the
    # declaration must survive being deduped here.
    carry: list[str] = []
    for base in reversed(cls.__mro__):
        for name in base.__dict__.get('__clone_extra__', ()):
            if name not in carry and name not in fields:
                carry.append(name)
    cls.__clone_carry__ = tuple(carry)  # type: ignore[attr-defined]

    compare = [mapping.get(field, field) for field in fields]
    compare += [name for name in carry if name not in compare]
    cls.__clone_compare__ = tuple(compare)  # type: ignore[attr-defined]


def clone_with(obj: 'BaseObject', overrides: dict[str, Any]) -> Any:
    cls = type(obj)
    base = _base_object()
    mapping = cls.__clone_map__
    posonly = cls.__clone_posonly__
    args: list[Any] = []
    kwargs: dict[str, Any] = {}
    for index, field in enumerate(cls.__clone_fields__):
        value = overrides.get(field, MISSING)
        if value is MISSING:
            value = _copied(getattr(obj, mapping.get(field, field)), base)
        if index < posonly:
            args.append(value)
        else:
            kwargs[field] = value
    clone = cls(*args, **kwargs)
    for name in cls.__clone_carry__:
        value = overrides.get(name, MISSING)
        if value is MISSING:
            value = _copied(getattr(obj, name), base)
        setattr(clone, name, value)
    from pyhtsw.compiler.reemission import note_clone

    note_clone(obj, clone)
    return clone
