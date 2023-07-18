"""
Assertion Utilities
"""


def assert_list_elements(the_list: list, elem_type):
    """
    Asserts that all elems in the list are of elem_type, then returns the list
    """
    if the_list:
        for elem in the_list:
            assert isinstance(elem, elem_type), f"got {type(elem)} instead"
        return the_list
    return []
