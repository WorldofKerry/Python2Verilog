"""
Type assertion utilities
"""
from typing import TYPE_CHECKING, Any, Optional, TypeGuard, TypeVar

ValueType = TypeVar("ValueType")  # pylint: disable=invalid-name
KeyType = TypeVar("KeyType")  # pylint: disable=invalid-name


def get_typed_list(list_: Optional[list], type_: ValueType):
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
    dict_: dict, key_type: KeyType, value_type: ValueType
) -> TypeGuard[dict[KeyType, ValueType]]:
    """
    Asserts that all key, values in dict_ are correctly typed,
    returns dict_ or {} if dict_ is None
    """
    get_typed(dict_, dict)
    for key, value in dict_.items():
        get_typed(key, key_type)
        get_typed(value, value_type)
    return True


def get_typed(obj: Any, type_: ValueType):
    """
    Asserts that obj is of type type_, then returns obj or None if obj is None
    """
    if not TYPE_CHECKING:
        assert isinstance(obj, type_), f"Expected {type_} got {type(obj)} instead"
    return obj
