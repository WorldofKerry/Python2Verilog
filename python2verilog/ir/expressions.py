"""
Intermediate Representation Expressions
Based on Verilog Syntax
"""
from __future__ import annotations
import copy
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
        return f"{self.to_string()}"

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
        super().__init__(str(value))


class Var(Expression):
    """
    Named-variable
    """

    def __init__(self, name: str):
        assert isinstance(name, str)
        super().__init__(name)


class State(Var):
    """
    State variable
    """


class BinOp(Expression):
    """
    <left> <op> <right>
    """

    def __init__(self, left: Expression, right: Expression, oper: str):
        self._left = left
        self._right = right
        assert oper in ["+", "-", "*", "/"], f"Unsupported operator {oper}"
        self._oper = oper
        super().__init__(f"({left.to_string()} {self._oper} {right.to_string()})")

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
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, right, "/")
