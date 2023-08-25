"""Parses Python Generator Functions to Intermediate Representation"""

from __future__ import annotations

import ast as pyast

from .. import ir
from ..utils.assertions import get_typed, get_typed_list
from ..utils.string import Indent, Lines


class Generator2Graph:
    """
    Parses python generator functions to Verilog AST
    """

    def __init__(
        self,
        context: ir.Context,
        done_state_name: str = "_statelmaoready",
    ):
        """
        Initializes the parser, does quick setup work
        """
        context.validate()
        self._context = get_typed(context, ir.Context)

        self._root = self.__parse_statements(
            stmts=context.py_ast.body,
            prefix="_state",
            nextt=ir.DoneNode(unique_id=done_state_name, name="done"),
        )

        self._context.entry_state = self._root.unique_id
        self._context.ready_state = done_state_name

    @property
    def root(self):
        """
        Returns the root of the IR Graph
        """
        return self._root

    @property
    def context(self):
        """
        Returns the context surrounding the Python generator function
        """
        return self._context

    @property
    def results(self):
        """
        Returns tuple containing the root and the context
        """
        return (self.root, self.context)

    def __parse_targets(self, nodes: list[pyast.expr]):
        """
        Warning: only single target on left-hand-side supported

        <target0, target1, ...> =
        """
        assert len(nodes) == 1
        node = nodes[0]
        if isinstance(node, pyast.Subscript):
            assert isinstance(node.value, pyast.Name)
            if not self._context.is_declared(node.value.id):
                self._context.add_global_var(ir.Var(py_name=node.value.id))
        elif isinstance(node, pyast.Name):
            if not self._context.is_declared(node.id):
                self._context.add_global_var(ir.Var(py_name=node.id))
        else:
            raise TypeError(f"Unsupported lvalue type {type(node)} {pyast.dump(node)}")
        return self.__parse_expression(node)

    def __parse_assign(self, node: pyast.Assign, prefix: str):
        """
        <target0, target1, ...> = <value>;
        """
        return ir.AssignNode(
            unique_id=prefix,
            lvalue=self.__parse_targets(node.targets),
            rvalue=self.__parse_expression(node.value),
        )

    def __parse_statements(
        self, stmts: list[pyast.stmt], prefix: str, nextt: ir.Element
    ):
        """
        Returns state of the first stmt in block

        Give it a prefix and name-mangling is handled for you

        {
            <statement0>
            <statement1>
            ...
        }
        """
        assert isinstance(stmts, list)
        assert isinstance(prefix, str)

        # builds backwards
        stmts.reverse()
        previous = self.__parse_statement(
            stmt=stmts[0], nextt=nextt, prefix=f"{prefix}_0"
        )
        for i in range(1, len(stmts)):
            previous = self.__parse_statement(
                stmt=stmts[i], nextt=previous, prefix=f"{prefix}_{i}"
            )
        return previous

    def __parse_statement(self, stmt: pyast.AST, nextt: ir.Element, prefix: str):
        """
        nextt represents the next operation in the control flow diagram.

        e.g. what does the program do after this current stmt (if-else/assignment)?

        returns the node that has been created

        <statement> (e.g. assign, for loop, etc., cannot be equated to)

        """
        get_typed(stmt, pyast.AST)
        get_typed(nextt, ir.Element)
        cur_node = None
        if isinstance(stmt, pyast.Assign):
            cur_node = self.__parse_assign(stmt, prefix=prefix)
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            cur_node.child = edge
        elif isinstance(stmt, pyast.Yield):
            cur_node = self.__parse_yield(stmt, prefix=prefix)
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            cur_node.child = edge
        elif isinstance(stmt, pyast.While):
            cur_node = self.__parse_while(stmt, nextt=nextt, prefix=prefix)
        elif isinstance(stmt, pyast.If):
            cur_node = self.__parse_ifelse(stmt=stmt, nextt=nextt, prefix=prefix)
        elif isinstance(stmt, pyast.Expr):
            cur_node = self.__parse_statement(
                stmt=stmt.value, nextt=nextt, prefix=prefix
            )
        elif isinstance(stmt, pyast.AugAssign):
            assert isinstance(
                stmt.target, pyast.Name
            ), "Error: only supports single target"
            edge = ir.ClockedEdge(unique_id=f"{prefix}_e", child=nextt)
            cur_node = ir.AssignNode(
                unique_id=prefix,
                lvalue=self.__parse_expression(stmt.target),
                rvalue=self.__parse_expression(
                    pyast.BinOp(stmt.target, stmt.op, stmt.value)
                ),
                child=edge,
            )
        else:
            raise TypeError(
                "Error: unexpected statement type", type(stmt), pyast.dump(stmt)
            )
        return cur_node

    def __parse_ifelse(self, stmt: pyast.If, nextt: ir.Element, prefix: str):
        """
        If statement
        """
        assert isinstance(stmt, pyast.If)

        then_node = self.__parse_statements(stmt.body, f"{prefix}_t", nextt)
        to_then = ir.ClockedEdge(
            unique_id=f"{prefix}_true_edge", name="True", child=then_node
        )
        if stmt.orelse:
            else_node = self.__parse_statements(stmt.orelse, f"{prefix}_f", nextt)
            to_else = ir.ClockedEdge(
                unique_id=f"{prefix}_false_edge", name="False", child=else_node
            )
            ifelse = ir.IfElseNode(
                unique_id=prefix,
                true_edge=to_then,
                false_edge=to_else,
                condition=self.__parse_expression(stmt.test),
            )
        else:
            to_else = ir.ClockedEdge(
                unique_id=f"{prefix}_false_edge", name="False", child=nextt
            )
            ifelse = ir.IfElseNode(
                unique_id=prefix,
                true_edge=to_then,
                false_edge=to_else,
                condition=self.__parse_expression(stmt.test),
            )

        return ifelse

    def __parse_while(self, stmt: pyast.While, nextt: ir.Element, prefix: str):
        """
        Converts while loop to a while-true-if-break loop
        """
        assert isinstance(stmt, pyast.While)

        loop_edge = ir.ClockedEdge(unique_id=f"{prefix}_edge", name="True")
        done_edge = ir.ClockedEdge(unique_id=f"{prefix}_f", name="False", child=nextt)

        ifelse = ir.IfElseNode(
            unique_id=f"{prefix}_while",
            condition=self.__parse_expression(stmt.test),
            true_edge=loop_edge,
            false_edge=done_edge,
        )
        body_node = self.__parse_statements(stmt.body, f"{prefix}_while", ifelse)
        loop_edge.child = body_node

        return ifelse

    def __parse_yield(self, node: pyast.Yield, prefix: str):
        """
        yield <value>;
        """
        if isinstance(node.value, pyast.Tuple):
            return ir.YieldNode(
                unique_id=prefix,
                name="Yield",
                stmts=[self.__parse_expression(c) for c in node.value.elts],
            )
        if isinstance(
            node.value, (pyast.Name, pyast.BinOp, pyast.Compare, pyast.UnaryOp)
        ):
            return ir.YieldNode(
                unique_id=prefix,
                name="Yield",
                stmts=[self.__parse_expression(c) for c in [node.value]],
            )
        raise TypeError(f"Expected tuple {type(node.value)}")

    def __parse_binop(self, expr: pyast.BinOp):
        """
        <left> <op> <right>
        """
        if isinstance(expr.op, pyast.Add):
            return ir.Add(
                self.__parse_expression(expr.left), self.__parse_expression(expr.right)
            )
        if isinstance(expr.op, pyast.Sub):
            return ir.Sub(
                self.__parse_expression(expr.left), self.__parse_expression(expr.right)
            )

        if isinstance(expr.op, pyast.Mult):
            return ir.Mul(
                self.__parse_expression(expr.left), self.__parse_expression(expr.right)
            )

        if isinstance(expr.op, pyast.FloorDiv):
            var_a = self.__parse_expression(expr.left)
            var_b = self.__parse_expression(expr.right)
            return ir.Ternary(
                condition=ir.BinOp(
                    left=ir.BinOp(left=var_a, right=var_b, oper="%"),
                    right=ir.Int(0),
                    oper="===",
                ),
                left=ir.BinOp(var_a, "/", var_b),
                right=ir.BinOp(
                    ir.BinOp(var_a, "/", var_b),
                    "-",
                    ir.BinOp(
                        ir.UBinOp(
                            ir.BinOp(var_a, "<", ir.Int(0)),
                            "^",
                            ir.BinOp(var_b, "<", ir.Int(0)),
                        ),
                        "&",
                        ir.Int(1),
                    ),
                ),
            )
        if isinstance(expr.op, pyast.Mod):
            var_a = self.__parse_expression(expr.left)
            var_b = self.__parse_expression(expr.right)
            return ir.Ternary(
                ir.UBinOp(var_a, "<", ir.Int(0)),
                ir.Ternary(
                    ir.UBinOp(var_b, ">=", ir.Int(0)),
                    ir.UnaryOp("-", ir.Mod(var_a, var_b)),
                    ir.Mod(var_a, var_b),
                ),
                ir.Ternary(
                    ir.UBinOp(var_b, "<", ir.Int(0)),
                    ir.UnaryOp("-", ir.Mod(var_a, var_b)),
                    ir.Mod(var_a, var_b),
                ),
            )
        raise TypeError(
            "Error: unexpected binop type", type(expr.op), pyast.dump(expr.op)
        )

    def __parse_expression(self, expr: pyast.AST):
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        if isinstance(expr, pyast.Constant):
            return ir.Int(expr.value)
        if isinstance(expr, pyast.Name):
            return ir.Var(py_name=expr.id)
        if isinstance(expr, pyast.Subscript):
            return self.__parse_subscript(expr)
        if isinstance(expr, pyast.BinOp):
            return self.__parse_binop(expr)
        if isinstance(expr, pyast.UnaryOp):
            if isinstance(expr.op, pyast.USub):
                return ir.UnaryOp("-", self.__parse_expression(expr.operand))
            raise TypeError(
                "Error: unexpected unaryop type", type(expr.op), pyast.dump(expr.op)
            )
        if isinstance(expr, pyast.Compare):
            return self.__parse_compare(expr)
        if isinstance(expr, pyast.BoolOp):
            if isinstance(expr.op, pyast.And):
                return ir.Expression(
                    f"({self.__parse_expression(expr.values[0]).to_string()}) \
                    && ({self.__parse_expression(expr.values[1]).to_string()})"
                )
        raise TypeError(
            "Error: unexpected expression type", type(expr), pyast.dump(expr)
        )

    def __parse_subscript(self, node: pyast.Subscript):
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return ir.Expression(
            f"{self.__parse_expression(node.value).to_string()}\
                [{self.__parse_expression(node.slice).to_string()}]"
        )

    def __parse_compare(self, node: pyast.Compare):
        """
        <left> <op> <comparators>
        """
        assert len(node.ops) == 1
        assert len(node.comparators) == 1

        if isinstance(node.ops[0], pyast.Lt):
            return ir.LessThan(
                self.__parse_expression(node.left),
                self.__parse_expression(node.comparators[0]),
            )
        if isinstance(node.ops[0], pyast.LtE):
            operator = "<="
        elif isinstance(node.ops[0], pyast.Gt):
            operator = ">"
        elif isinstance(node.ops[0], pyast.GtE):
            operator = ">="
        elif isinstance(node.ops[0], pyast.NotEq):
            operator = "!=="
        elif isinstance(node.ops[0], pyast.Eq):
            operator = "==="
        else:
            raise TypeError(
                "Error: unknown operator", type(node.ops[0]), pyast.dump(node.ops[0])
            )
        return ir.BinOp(
            left=self.__parse_expression(node.left),
            oper=operator,
            right=self.__parse_expression(node.comparators[0]),
        )
