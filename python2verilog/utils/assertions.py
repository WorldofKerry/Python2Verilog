"""
Type assertion utilities
"""


def assert_list_type(list_: list, type_: type):
    """
    Asserts that all elems in list_ are of type_, then returns list_ or [] if list_ is None
    """
    if list_:
        for elem in list_:
            assert_type(elem, type_)
        return list_
    return []


def assert_type(obj, type_: type):
    """
    Asserts that obj is of type type_, then returns obj or None if obj is None
    """
    if obj:
        assert isinstance(obj, type_), f"expected {type_} got {type(obj)} instead"
        return obj
    return None
