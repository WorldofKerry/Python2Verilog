"""Parses Python Generator Functions to Intermediate Representation"""

from __future__ import annotations
import copy
import warnings
import ast as pyast
from typing import Optional

from .. import ir
from ..utils.string import Lines, Indent
from ..utils.assertions import assert_type, assert_list_type


class Generator2Graph:
    """
    Parses python generator functions to Verilog AST
    """

    def __init__(self, python_func: pyast.FunctionDef):
        """
        Initializes the parser, does quick setup work
        """
        self._name = assert_type(python_func.name, str)
        self._context = ir.Context(name=assert_type(python_func.name, str))
        self._python_func = python_func

        assert python_func.returns is not None, "Write a return type-hint for function"
        self._context.output_vars = self.__generate_output_vars(python_func.returns, "")
        self._context.input_vars = [var.arg for var in self._python_func.args.args]

        self._state_var = ir.State("_state")
        self._states = ir.Case(
            self._state_var,
            [],
        )

        done_state = self.__add_state_var(ir.State("_statedone"))
        self._root = self.__parse_statements(
            list(python_func.body),
            "",
            ir.Edge(
                id_="_edgedone",
                name="DONE",
                next_node=ir.Node(id_="_statelmaodone"),
            ),
        )

        self._states.case_items.append(
            ir.CaseItem(
                done_state,
                [ir.NonBlockingSubsitution(ir.Var("_done"), ir.Int(1))],
            )
        )

    def __str__(self):
        return self.generate_verilog().to_string()

    def __add_state_var(self, state: ir.State):
        self._context.state_vars.append(state)
        return state

    def get_root(self):
        """
        Gets the root of the IR tree
        """
        return copy.deepcopy(self._states)

    @staticmethod
    def __generate_output_vars(node: pyast.AST, prefix: str):
        """
        Generates the yielded variables of the function
        """
        assert isinstance(node, pyast.Subscript)
        if isinstance(node.slice, pyast.Tuple):
            return [f"{prefix}_out{str(i)}" for i in range(len(node.slice.elts))]
        if isinstance(node.slice, pyast.Name):
            return [f"{prefix}_out0"]
        raise NotImplementedError(
            f"Unexpected function return type hint {type(node.slice)}, {pyast.dump(node.slice)}"
        )

    def __add_global_var(self, initial_value: str, name: str):
        """
        Adds global variables
        """
        self._context.global_vars[name] = initial_value
        return name

    def get_context(self):
        """
        Gets the context of the Python function
        """
        for i, var in enumerate(self._context.state_vars):
            self.__add_global_var(str(i), var.to_string())
        return self._context

    def get_results(self):
        """
        Gets root of IR and Context
        """
        return (self.get_root(), self.get_context())

    def generate_verilog(self, indent: int = 0):
        """
        Generates the verilog (does the most work, calls other functions)
        """
        stmt_lines = (
            self._states.to_lines(),
            Lines(),
        )
        module_lines = self.__stringify_module()
        decl_lines = self.__stringify_declarations(self._context.global_vars)
        always_blk_lines = self.__stringify_always_block()
        decl_and_always_blk_lines = (
            decl_lines[0].concat(always_blk_lines[0]),
            decl_lines[1].concat(always_blk_lines[1]),
        )  # TODO: there should be a function for this
        init_lines = self.__stringify_initialization(self._context.global_vars)

        return Lines.nestify(
            [
                module_lines,
                decl_and_always_blk_lines,
                init_lines,
                stmt_lines,
            ],
            indent,
        )

    @staticmethod
    def __stringify_always_block():
        """
        always @(posedge _clock) begin
        end
        """
        return (
            Lines(["always @(posedge _clock) begin", Indent(1) + "_valid <= 0;"]),
            Lines(["end"]),
        )

    @staticmethod
    def __stringify_initialization(global_vars: dict[str, str]):
        """
        if (_start) begin
            <var> = <value>;
            ...
        end else begin
        ...
        end
        """
        start_lines, end_lines = Lines(), Lines()
        start_lines += "if (_start) begin"
        start_lines += Indent(1) + "_done <= 0;"
        for var in global_vars:
            start_lines += Indent(1) + f"{var} <= {global_vars[var]};"
        start_lines += "end else begin"
        end_lines += "end"
        return (start_lines, end_lines)

    @staticmethod
    def __stringify_declarations(global_vars: dict[str, str]) -> tuple[Lines, Lines]:
        """
        reg [31:0] <name>;
        ...
        """
        return (Lines([f"reg signed [31:0] {v};" for v in global_vars]), Lines())

    def __stringify_module(self) -> tuple[Lines, Lines]:
        """
        module <name>(...);

        endmodule
        """
        start_lines, end_lines = Lines(), Lines()
        assert self._name not in {
            "default",
            "module",
            "output",
            "function",
        }  # Verilog Reserved Keywords
        start_lines += f"module {self._name}("
        start_lines += Indent(1) + "input wire _clock,"
        start_lines += Indent(1) + "input wire _start,"
        for var in self._python_func.args.args:
            start_lines += Indent(1) + f"input wire signed [31:0] {var.arg},"
        for var in self._context.output_vars:
            start_lines += Indent(1) + f"output reg signed [31:0] {var},"
        start_lines += Indent(1) + "output reg _done,"
        start_lines += Indent(1) + "output reg _valid"
        start_lines += ");"
        end_lines += "endmodule"
        return (start_lines, end_lines)

    def __parse_targets(self, nodes: list[pyast.AST]):
        """
        Warning: only single target on left-hand-side supported

        <target0, target1, ...> =
        """
        assert len(nodes) == 1
        node = nodes[0]
        if isinstance(node, pyast.Subscript):
            assert isinstance(node.value, pyast.Name)
            if node.value.id not in set(
                [
                    *self._context.global_vars,
                    *self._context.output_vars,
                    *self._context.input_vars,
                ]
            ):
                warnings.warn(
                    str(
                        set(
                            [
                                *self._context.global_vars,
                                *self._context.output_vars,
                                *self._context.input_vars,
                            ]
                        )
                    )
                )
                self.__add_global_var(str(0), node.value.id)
        elif isinstance(node, pyast.Name):
            if not self._context.is_declared(node.id):
                self.__add_global_var(str(0), node.id)
        else:
            raise TypeError(f"Unsupported lvalue type {type(node)} {pyast.dump(node)}")
        return self.__parse_expression(node)

    def __parse_assign(self, node: pyast.Assign, prefix: str):
        """
        <target0, target1, ...> = <value>;
        """
        return ir.AssignNode(
            id_=prefix,
            lvalue=self.__parse_targets(list(node.targets)),
            rvalue=self.__parse_expression(node.value),
        )

    def __parse_statements(self, stmts: list[pyast.AST], prefix: str, nextt: ir.Edge):
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
        # builds link from the returned node to next_node
        stmts.reverse()
        previous = self.__parse_statement(
            stmt=stmts[0], nextt=nextt, prefix=f"{prefix}_0"
        )
        for i in range(1, len(stmts)):
            edge = ir.Edge(id_=f"{prefix}_e{i}", next_node=previous)
            previous = self.__parse_statement(
                stmt=stmts[i], nextt=edge, prefix=f"{prefix}_{i}"
            )

        return previous

    def __parse_statement(self, stmt: pyast.AST, nextt: ir.Edge, prefix: str):
        """
        next_node represents the next operation in the control flow diagram.

        e.g. what does the program do after this current stmt (if-else/assignment)?

        <statement> (e.g. assign, for loop, etc., cannot be equated to)

        """
        assert_type(stmt, pyast.AST)
        assert_type(nextt, ir.Edge)
        cur_node = None
        if isinstance(stmt, pyast.Assign):
            cur_node = self.__parse_assign(stmt, prefix=prefix)
            cur_node.set_edge(nextt)
        elif isinstance(stmt, pyast.Yield):
            cur_node = self.__parse_yield(stmt, prefix=prefix)
            cur_node.set_edge(nextt)
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
            cur_node = ir.AssignNode(
                id_=prefix,
                lvalue=self.__parse_expression(stmt.target),
                rvalue=self.__parse_expression(
                    pyast.BinOp(stmt.target, stmt.op, stmt.value)
                ),
                edge=nextt,
            )
        else:
            raise TypeError(
                "Error: unexpected statement type", type(stmt), pyast.dump(stmt)
            )
        return cur_node

    def __parse_ifelse(self, stmt: pyast.If, nextt: ir.Edge, prefix: str):
        """
        If statement
        """
        assert isinstance(stmt, pyast.If)
        then_node = self.__parse_statements(list(stmt.body), f"{prefix}_t", nextt)
        else_node = self.__parse_statements(list(stmt.orelse), f"{prefix}_f", nextt)

        then_edge = ir.Edge(id_=f"{prefix}_true_edge", name="True", next_node=then_node)
        else_edge = ir.Edge(
            id_=f"{prefix}_false_edge", name="False", next_node=else_node
        )

        ifelse = ir.IfElseNode(
            id_=prefix,
            then_edge=then_edge,
            else_edge=else_edge,
            condition=self.__parse_expression(stmt.test),
        )
        return ifelse

    def __parse_while(self, stmt: pyast.While, nextt: ir.Edge, prefix: str):
        """
        Converts while loop to a while-true-if-break loop
        """
        assert isinstance(stmt, pyast.While)

        body_edge = ir.Edge(id_=f"{prefix}_edge", name="True")
        recurse_edge = ir.Edge(id_=f"{prefix}_recur", name="Recurse")
        body_node = self.__parse_statements(
            list(stmt.body), f"{prefix}_while", recurse_edge
        )
        body_edge.set_next_node(body_node)

        ifelse = ir.IfElseNode(
            id_=f"{prefix}_while",
            condition=self.__parse_expression(stmt.test),
            then_edge=body_edge,
            else_edge=nextt,
        )
        recurse_edge.set_next_node(ifelse)

        return ifelse

    def __parse_yield(self, node: pyast.Yield, prefix: str):
        """
        Warning: may not work for single output

        Warning: requires self.yieldVars to be complete

        yield <value>;
        """
        assert isinstance(node.value, pyast.Tuple)
        return ir.YieldNode(
            id_=prefix,
            name="Yield",
            stmts=[self.__parse_expression(c) for c in node.value.elts],
        )

    def __parse_binop_improved(self, expr: pyast.BinOp):
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

        if isinstance(expr.op, (pyast.Div, pyast.FloorDiv)):
            return ir.Div(
                self.__parse_expression(expr.left), self.__parse_expression(expr.right)
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
            return ir.Var(expr.id)
        if isinstance(expr, pyast.Subscript):
            return self.__parse_subscript(expr)
        if isinstance(expr, pyast.BinOp):
            # Special case for floor division with  2 on right-hand-side
            # Due to Verilog handling negative division "rounding"
            # differently than Python floor division
            # e.g. Verilog: -5 / 2 == -2, Python: -5 // 2 == -3
            if (
                isinstance(expr.op, pyast.FloorDiv)
                and isinstance(expr.right, pyast.Constant)
                and expr.right.value > 0
                and expr.right.value % 2 == 0
            ):
                a_var = self.__parse_expression(expr.left).to_string()
                b_var = expr.right.value
                return ir.Expression(
                    f"({a_var} > 0) ? ({a_var} / {b_var}) : ({a_var} / {b_var} - 1)"
                )
            return self.__parse_binop_improved(expr)
        if isinstance(expr, pyast.UnaryOp):
            if isinstance(expr.op, pyast.USub):
                return ir.Expression(
                    f"-({self.__parse_expression(expr.operand).to_string()})"
                )
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
            operator = "<"
        elif isinstance(node.ops[0], pyast.LtE):
            operator = "<="
        elif isinstance(node.ops[0], pyast.Gt):
            operator = ">"
        elif isinstance(node.ops[0], pyast.GtE):
            operator = ">="
        else:
            raise TypeError(
                "Error: unknown operator", type(node.ops[0]), pyast.dump(node.ops[0])
            )
        return ir.Expression(
            f"{self.__parse_expression(node.left).to_string()} {operator}"
            f" {self.__parse_expression(node.comparators[0]).to_string()}"
        )
