"""
Type assertion utilities
"""
from typing import Optional, Any


def assert_list_type(list_: Optional[list], type_: type):
    """
    Asserts that all elems in list_ are of type_, then returns list_ or [] if list_ is None
    """
    if list_:
        assert_type(list_, list)
        for elem in list_:
            assert_type(elem, type_)
        return list_
    return []


def assert_dict_type(dict_: Optional[dict], key_type: type, value_type: type):
    """
    Asserts that all key, values in dict_ are correctly typed,
    returns dict_ or {} if dict_ is None
    """
    if dict_:
        assert_type(dict_, dict)
        for key, value in dict_.items():
            assert_type(key, key_type)
            assert_type(value, value_type)
        return dict_
    return {}


def assert_type(obj: Any, type_: type):
    """
    Asserts that obj is of type type_, then returns obj or None if obj is None
    """
    if obj:
        assert isinstance(obj, type_), f"expected {type_} got {type(obj)} instead"
    return obj
