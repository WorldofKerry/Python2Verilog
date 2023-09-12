"""
Implementation of generic base classes for __repr__ and __str__
"""


from typing import Any


def pretty_dict(dic: dict[Any, Any], indent: int = 0) -> str:
    """
    Returns pretty-formatted stringified dict
    """
    result = "{\n"
    for key, value in dic.items():
        result += "\t" * (indent + 1) + str(key) + ": "
        if isinstance(value, dict):
            result += pretty_dict(value, indent + 1)
        else:
            result += str(value) + ",\n"
    return result + "\t" * (indent) + "}\n"


class GenericRepr:
    """
    Implements a generic __repr__ based on self.__dict__
    """

    def __repr__(self):
        items = [f"{key}=({repr(value)})" for key, value in self._repr().items()]
        return f"{self.__class__.__name__}({','.join(items)})"

    def _repr(self):
        """
        Representation of self

        To print recursive types
        """
        return self.__dict__


class GenericReprAndStr(GenericRepr):
    """
    Implements a generic __repr__ and __str__ based on self.__dict__
    """

    def __str__(self):
        return f"{self.__class__.__name__}\n{pretty_dict(self._repr())}"
