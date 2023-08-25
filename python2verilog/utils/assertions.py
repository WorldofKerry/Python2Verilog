"""
Type assertion utilities
"""
import sys
import types
from typing import Any, Optional, Type, TypeAlias, TypeGuard, TypeVar, Union

ValueType = TypeVar("ValueType")  # pylint: disable=invalid-name
KeyType = TypeVar("KeyType")  # pylint: disable=invalid-name

# pylint: disable=used-before-assignment
if sys.version_info >= (3, 10):
    _ClassInfo: TypeAlias = Union[type, types.UnionType, tuple["_ClassInfo", ...]]
else:
    _ClassInfo: TypeAlias = Union[type, tuple["_ClassInfo", ...]]


def get_typed_list(list_: Optional[list], type_: Type[ValueType]):
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
    dict_: dict, key_type: _ClassInfo, value_type: _ClassInfo
) -> TypeGuard[dict[KeyType, ValueType]]:
    """
    Asserts that all key, values in dict_ are correctly typed,
    returns dict_ or {} if dict_ is None
    """
    assert_typed(dict_, dict)
    for key, value in dict_.items():
        assert_typed(key, key_type)
        assert_typed(value, value_type)
    return True


def assert_typed(obj: Any, type_: _ClassInfo) -> TypeGuard[_ClassInfo]:
    """
    Type guard for type
    """
    assert isinstance(obj, type_), f"Expected {type_} got {type(obj)} instead"
    return True


def get_typed(obj: ValueType, type_: _ClassInfo):
    """
    Asserts that obj is of type type_, then returns obj or None if obj is None
    """
    if obj:
        assert_typed(obj, type_)
    return obj
