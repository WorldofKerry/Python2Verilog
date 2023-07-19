"""
Intermediate Representation Expressions
Based on Verilog Syntax
"""


class Expression:
    """
    A String (that can be equated to something)
    """

    def __init__(self, string: str):
        self.string = string

    def to_string(self):
        """
        To Verilog
        """
        return self.string


class BinOp(Expression):
    """
    <left> <op> <right>
    """

    def __init__(self, left: Expression, right: Expression, oper: str):
        self.left = left
        self.right = right
        assert oper in ["+", "-", "*", "/"], f"Unsupported operator {oper}"
        self.oper = oper
        super().__init__(f"({left} {self.oper} {right})")


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
