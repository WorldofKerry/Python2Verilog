"""
Intermediate Representation Expressions
Based on Verilog Syntax
"""


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

    def __repr__(self):
        return f"({self.to_string()})"


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
        self.left = left
        self.right = right
        assert oper in ["+", "-", "*", "/"], f"Unsupported operator {oper}"
        self.oper = oper
        super().__init__(f"({left.to_string()} {self.oper} {right.to_string()})")


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
