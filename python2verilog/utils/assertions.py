"""
Type assertion utilities
"""
import sys
from typing import Any, Optional, Type, TypeVar, Union, cast

try:
    from typing import TypeAlias, TypeGuard
except ImportError:
    from typing_extensions import TypeAlias, TypeGuard

_ValueType = TypeVar("_ValueType")  # pylint: disable=invalid-name
_KeyType = TypeVar("_KeyType")  # pylint: disable=invalid-name
_ClassInfo: TypeAlias = Union[type, tuple["_ClassInfo", ...]]


def get_typed_list(
    list_: Optional[list[_ValueType]], type_: Type[_ValueType]
) -> list[_ValueType]:
    """
    Asserts that all elems in list_ are of type_, then returns list_ or [] if list_ is None
    """
    if list_:
        get_typed(list_, list)
        for elem in list_:
            get_typed(elem, type_)
        return list_
    return []


def assert_typed_dict(
    dict_: dict[Any, Any],
    key_type: Type[_KeyType],
    value_type: Type[_ValueType],
) -> TypeGuard[dict[_KeyType, _ValueType]]:
    """
    Asserts that all key, values in dict_ are correctly typed,
    returns dict_ or {} if dict_ is None
    """
    return (
        isinstance(dict_, dict)
        and all(isinstance(x, key_type) for x in dict_.keys())
        and all(isinstance(x, value_type) for x in dict_.values())
    )


def assert_typed(obj: Any, type_: Type[_ValueType]) -> TypeGuard[_ValueType]:
    """
    Type guard for type
    """
    assert isinstance(obj, type_), f"Expected {type_} got {type(obj)} instead {obj}"
    return True


def get_typed(obj: Any, type_: Type[_ValueType]) -> Union[_ValueType, None]:
    """
    Asserts that obj is of type type_, then returns obj or None if obj is None
    """
    if obj is None:
        return None
    assert assert_typed(obj, type_)
    return obj


def get_typed_strict(obj: Any, type_: Type[_ValueType]) -> _ValueType:
    """
    Asserts that obj is of type type_
    """
    assert assert_typed(obj, type_)
    return obj
