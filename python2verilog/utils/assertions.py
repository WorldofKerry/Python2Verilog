"""
Type assertion utilities
"""
import sys
import types
from typing import Any, Optional, Type, TypeVar, cast

try:
    from typing import TypeAlias, TypeGuard
except ImportError:
    from typing_extensions import TypeAlias, TypeGuard

_ValueType = TypeVar("_ValueType")  # pylint: disable=invalid-name
_KeyType = TypeVar("_KeyType")  # pylint: disable=invalid-name
_ClassInfo: TypeAlias = type | types.UnionType | tuple["_ClassInfo", ...]


def get_typed_list(list_: Optional[list[_ValueType]], type_: Type[_ValueType]):
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
    dict_: dict[_KeyType, _ValueType], key_type: _KeyType, value_type: _ValueType
) -> TypeGuard[dict[_KeyType, _ValueType]]:
    """
    Asserts that all key, values in dict_ are correctly typed,
    returns dict_ or {} if dict_ is None
    """
    assert_typed(dict_, dict)
    for key, value in dict_.items():
        assert_typed(key, cast(_ClassInfo, key_type))
        assert_typed(value, cast(_ClassInfo, value_type))
    return True


def assert_typed(obj: Any, type_: _ClassInfo) -> TypeGuard[_ClassInfo]:
    """
    Type guard for type
    """
    assert isinstance(obj, type_), f"Expected {type_} got {type(obj)} instead {obj}"
    return True


def get_typed(obj: _ValueType, type_: _ValueType):
    """
    Asserts that obj is of type type_, then returns obj or None if obj is None
    """
    return get_typed_optional(obj, type_)


def get_typed_optional(obj: _ValueType, type_: _ValueType):
    """
    Asserts that obj is of type type_, then returns obj or None if obj is None
    """
    if obj is not None:
        get_typed_strict(obj, type_)
        return obj
    assert obj is None
    return None


def get_typed_strict(obj: _ValueType, type_: _ValueType):
    """
    Asserts that obj is of type type_
    """
    assert_typed(obj, cast(_ClassInfo, type_))
    return obj
