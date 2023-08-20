"""
Special decorator primatives
"""

from types import FunctionType
from functools import wraps


def decorator_with_args(func):
    """
    a decorator decorator, allowing the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator

    Note: can't distinguish between a function as a parameter vs
    a function to-be decorated
    """

    @wraps(func)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], FunctionType):
            # actual decorated function
            return func(args[0])
        # decorator arguments
        return lambda realf: func(realf, *args, **kwargs)

    return new_dec
