"""
Based on paper

https://link.springer.com/chapter/10.1007/978-3-642-37051-9_6
"""

import ast as pyast

from python2verilog.exceptions import UnsupportedSyntaxError
from python2verilog.utils.typed import guard


class Expression:
    """
    Expression
    """


class Var:
    """
    Var
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Var):
            return self.name == __value.name
        return False

    def __repr__(self) -> str:
        return f"{self.name}"

    def __hash__(self) -> int:
        return hash(self.name)


class BinOp:
    """
    BinOp
    """

    def __init__(self, left: Expression, oper: str, right: Expression) -> None:
        self.left = left
        self.right = right
        self.oper = oper

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, BinOp):
            return (
                self.oper == __value.oper
                and self.left == __value.left
                and self.right == __value.right
            )
        return False

    def __repr__(self) -> str:
        return f"{self.left} {self.oper} {self.right}"

    def __hash__(self) -> int:
        return hash(self.oper)  # improve


class Int:
    """
    Int
    """

    def __init__(self, value: int) -> None:
        self.value = value

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Int):
            return self.value == __value.value
        return False

    def __repr__(self) -> str:
        return f"{self.value}"

    def __hash__(self) -> int:
        return hash(self.value)


class SSA:
    def __init__(self) -> None:
        self.current_def: dict[Expression, Var] = {}
        self.var_mapping: dict[str, Var] = {}

        self.block = "bruv_lmao"
        self.counter = 0

    def next_var(self) -> Var:
        """
        Next var
        """
        self.counter += 1
        return Var(f"v{self.counter}")

    def parse_stmts(self, block: str, stmts: list[pyast.stmt]):
        """
        Parse statements
        """
        for stmt in stmts:
            assert guard(stmt, pyast.Assign)
            self._parse_stmt(stmt)
        return self.current_def

    def _parse_stmt(self, stmt: pyast.Assign):
        """
        Parse statement
        """
        expr = self._parse_expression(stmt.value)
        self.var_mapping[stmt.targets[0].id] = expr
        print(self.var_mapping)
        print(self.current_def)

    def _parse_expression(self, expr: pyast.expr) -> Expression:
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        if isinstance(expr, pyast.Constant):
            temp = Int(expr.value)
            if temp in self.current_def:
                return self.current_def[temp]
            self.current_def[temp] = self.next_var()
            return self.current_def[temp]

        if isinstance(expr, pyast.Name):
            return self.read_variable(expr.id)

        if isinstance(expr, pyast.BinOp):
            return self._parse_binop(expr)

        raise RuntimeError()

    def _parse_binop(self, expr: pyast.BinOp) -> Expression:
        """
        <left> <op> <right>

        With special case for floor division
        """
        if isinstance(expr.op, pyast.Add):
            temp = BinOp(
                self._parse_expression(expr.left),
                "+",
                self._parse_expression(expr.right),
            )
            if temp in self.current_def:
                return self.current_def[temp]
            self.current_def[temp] = self.next_var()
            return self.current_def[temp]
        raise RuntimeError()

    def read_variable(self, name: str):
        """
        Read variable
        """
        if name in self.var_mapping:
            return self.var_mapping[name]
        print(f"External {name}")
        self.var_mapping[name] = self.next_var()
        return self.var_mapping[name]
