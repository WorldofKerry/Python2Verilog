"""
Intermediate Representation Expressions
Based on Verilog Syntax
"""
from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Optional
from ..utils.assertions import assert_type, assert_list_type


class Expression:
    """
    A String (that can be equated to something)
    """

    def __init__(self, string: str):
        assert isinstance(string, str)
        self.string = string

    def to_string(self):
        """
        To String
        """
        return self.string

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        items = [f"{key}=({value})" for key, value in self.__dict__.items()]
        return f"{self.__class__.__name__}({','.join(items)})"

    def __eq__(self, other: object):
        if assert_type(other, Expression):
            return str(self) == str(other)
        return False

    def __hash__(self):
        return hash(str(self))


class Int(Expression):
    """
    Integer literal
    """

    def __init__(self, value: int):
        assert isinstance(value, int)
        super().__init__(f"$signed({str(value)})")


class Var(Expression):
    """
    Named-variable
    """

    def __init__(
        self,
        py_name: str,
        ver_name: str = "",
        width: int = 32,
        isSigned: bool = True,
        initial_value: str = "0",
    ):
        if ver_name == "":
            ver_name = "_" + py_name

        self.ver_name = assert_type(ver_name, str)
        self.py_name = assert_type(py_name, str)
        self.width = assert_type(width, int)
        self.is_signed = assert_type(isSigned, bool)
        self.initial_value = initial_value

        super().__init__(py_name)


class State(Var):
    """
    State variable
    """


class Ternary(Expression):
    """
    <condition> ? <left> : <right>
    """

    def __init__(self, condition: Expression, left: Expression, right: Expression):
        self.condition = condition
        self.left = left
        self.right = right
        super().__init__(str(self))

    def to_string(self):
        return f"{str(self.condition)} ? {str(self.left)} : {str(self.right)}"


class BinOp(Expression):
    """
    <left> <op> <right>
    """

    def __init__(self, left: Expression, right: Expression, oper: str):
        self._left = assert_type(left, Expression)
        self._right = assert_type(right, Expression)
        self._oper = assert_type(oper, str)
        super().__init__(str(self))

    @property
    def left(self):
        """
        lvalue
        """
        return copy.deepcopy(self._left)

    @left.setter
    def left(self, other: Expression):
        self._left = assert_type(other, Expression)

    @property
    def right(self):
        """
        rvalue
        """
        return copy.deepcopy(self._right)

    @right.setter
    def right(self, other: Expression):
        self._right = assert_type(other, Expression)

    def to_string(self):
        return f"({self._left.to_string()} {self._oper} {self._right.to_string()})"


class Add(BinOp):
    """
    <left> + <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, right, "+")


class Sub(BinOp):
    """
    <left> - <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, right, "-")


class Mul(BinOp):
    """
    <left> * <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, right, "*")


class Div(BinOp):
    """
    <left> / <right>
    Truncates decimals
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, right, "/")


class Pow(BinOp):
    """
    <left> ** <right>
    <left> to the power of <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, right, "**")


class Mod(BinOp):
    """
    <left> % <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, right, "%")


class LessThan(BinOp):
    """
    <left> < <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, right, "<")
