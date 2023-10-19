"""
Exceptions
"""
import ast

from python2verilog.ir.expressions import Var


class UnknownValueError(Exception):
    """
    An unexpected 'x' or 'z' was encountered in simulation
    """


class UnsupportedSyntaxError(Exception):
    """
    Python syntax was not within the supported subset
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Python syntax was not within the supported subset",
            *args,
        )

    @classmethod
    def from_pyast(cls, node: ast.AST):
        """
        Based on AST error
        """
        inst = cls(f"Unsupported Python syntax {ast.dump(node)}")
        return inst


class StaticTypingError(Exception):
    """
    Variable changed type dynamically.
    Currently requires strongly typed variables.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            *args,
        )


class TypeInferenceError(Exception):
    """
    Type inferrence failed, either use the function in code or provide type hints
    """

    def __init__(self, *args: object) -> None:
        msg = (
            "Input/output type inferrence failed, "
            "either use the function in Python code or provide type hints",
        )

        super().__init__(" ".join(map(str, (*msg, *args))))
