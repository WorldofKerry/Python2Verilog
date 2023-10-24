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


class SSA:
    def __init__(self) -> None:
        self.current_def: dict[str, dict[str, Expression]] = {}
        self.var_mapping = {}
        self.block = "bruvlamo"

    def parse_stmts(self, block: str, stmts: list[pyast.stmt]):
        """
        Parse statements
        """
        number = 0
        ssa = []
        for stmt in stmts:
            assert guard(stmt, pyast.Assign)
            var_name = Var(f"v{number}")
            var_value = self._parse_expression(stmt.value)
            self.var_mapping[stmt.targets[0].id] = var_name
            ssa.append(f"{var_name}: {var_value}")
            self.write_variable(var_name, self.block, var_value)
            number += 1
        return "\n" + "\n".join(ssa)

    def write_variable(self, variable: str, block: str, value: Expression):
        assert guard(variable, Var)
        if variable not in self.current_def:
            self.current_def[variable] = {}
        self.current_def[variable][block] = value

    def read_variable(self, variable: str, block: str):
        assert guard(variable, Var)
        if variable in self.current_def:
            if block in self.current_def[variable]:
                return variable
                # return self.current_def[variable][block]
        return variable

    def _parse_expression(self, expr: pyast.expr) -> Expression:
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        if isinstance(expr, pyast.Constant):
            return Int(expr.value)
        if isinstance(expr, pyast.Name):
            return self.read_variable(
                self.var_mapping.get(expr.id, Var(expr.id)), self.block
            )
        if isinstance(expr, pyast.BinOp):
            return self._parse_binop(expr)
        raise RuntimeError()

    def _parse_binop(self, expr: pyast.BinOp) -> Expression:
        """
        <left> <op> <right>

        With special case for floor division
        """
        if isinstance(expr.op, pyast.Add):
            return BinOp(
                self._parse_expression(expr.left),
                "+",
                self._parse_expression(expr.right),
            )
        raise RuntimeError()
