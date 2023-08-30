"""
Intermediate Representation Expressions

Represents the subset of Python expressions
that are synthesizable

"""
from __future__ import annotations

import copy

from ..utils.assertions import get_typed, get_typed_list
from ..utils.generics import GenericRepr


class Expression(GenericRepr):
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

    def __eq__(self, other: object):
        if get_typed(other, Expression):
            return str(self) == str(other)
        return False

    def __hash__(self):
        return hash(str(self))


class Int(Expression):
    """
    Signed integer literal
    """

    def __init__(self, value: int):
        assert isinstance(value, int)
        super().__init__(f"$signed({str(value)})")


class UInt(Expression):
    """
    Unsigned integer literal
    """

    def __init__(self, value: int):
        assert isinstance(value, int)
        super().__init__(str(value))


class Unknown(Expression):
    """
    Unknown or "don't care" value
    """

    def __init__(self):
        super().__init__("'x")


class Var(Expression):
    """
    Named-variable
    """

    def __init__(
        self,
        py_name: str,
        ver_name: str = "",
        width: int = 32,
        is_signed: bool = True,
        initial_value: str = "0",
        **_,
    ):
        if ver_name == "":
            ver_name = "_" + py_name

        self.ver_name = get_typed(ver_name, str)
        self.py_name = get_typed(py_name, str)  # Matches I/O of Verilog
        self.width = get_typed(width, int)
        self.is_signed = get_typed(is_signed, bool)
        self.initial_value = initial_value

        super().__init__(ver_name)


class State(Var):
    """
    State variable
    """

    def __init__(
        self, name, width: int = 32, isSigned: bool = True, initial_value: str = "0"
    ):
        super().__init__(name, name, width, isSigned, initial_value)


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


class UBinOp(Expression):
    """
    Unsigned BinOp
    Is usually better for comparators
    """

    def __init__(self, left: Expression, oper: str, right: Expression):
        self._left = get_typed(left, Expression)
        self._right = get_typed(right, Expression)
        self._oper = get_typed(oper, str)
        super().__init__(self.__class__.__name__)

    @property
    def left(self):
        """
        lvalue
        """
        return copy.deepcopy(self._left)

    @left.setter
    def left(self, other: Expression):
        self._left = get_typed(other, Expression)

    @property
    def right(self):
        """
        rvalue
        """
        return copy.deepcopy(self._right)

    @right.setter
    def right(self, other: Expression):
        self._right = get_typed(other, Expression)

    def to_string(self):
        return f"({self._left.to_string()} {self._oper} {self._right.to_string()})"


class BinOp(UBinOp):
    """
    $signed(<left> <op> <right>)
    """

    def to_string(self):
        return "$signed" + super().to_string()


class Add(BinOp):
    """
    <left> + <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, "+", right)


class Sub(BinOp):
    """
    <left> - <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, "-", right)


class Mul(BinOp):
    """
    <left> * <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, "*", right)


class Div(BinOp):
    """
    <left> / <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, "/", right)


class LessThan(UBinOp):
    """
    <left> < <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, "<", right)


class Pow(UBinOp):
    """
    <left> ** <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, "**", right)


class Mod(UBinOp):
    """
    <left> % <right>
    """

    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, "%", right)


class UnaryOp(Expression):
    """
    <op>(<expr>)
    """

    def __init__(self, oper: str, expr: Expression):
        self.oper = get_typed(oper, str)
        self.expr = get_typed(expr, Expression)
        super().__init__(self.__class__.__name__)

    def to_string(self):
        """
        string
        """
        return f"{self.oper}({self.expr})"
