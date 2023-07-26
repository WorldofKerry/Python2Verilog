"""Parses Python Generator Functions to Intermediate Representation"""

from __future__ import annotations
import copy
import warnings
import ast as pyast
from typing import Optional

from .. import ir
from ..utils.string import Lines, Indent
from ..utils.assertions import assert_type, assert_list_type


class Generator2List:
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

        self.state_var = ir.State("_state")
        self.states = ir.Case(
            self.state_var,
            [],
        )

        done_state = self.__add_state_var(ir.State("_statedone"))
        self._root = self.__parse_statements(
            list(python_func.body), "_state", done_state
        )

        self.states.case_items.append(
            ir.CaseItem(
                done_state,
                [ir.NonBlockingSubsitution(ir.Var("_done"), ir.Int(1))],
            )
        )

    def __str__(self):
        return self.generate_verilog().to_string()

    wow_counter = 0

    def __add_state_var(self, state: ir.State):
        if state.string == "_state4while4":
            self.wow_counter += 1
            # if self.wow_counter == 1:
            #     raise Exception()
        self._context.state_vars.append(state)
        return state

    def get_root(self):
        """
        Gets the root of the IR tree
        """
        return copy.deepcopy(self.states)

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
        self.__add_global_var(str(1), self.state_var.to_string())  # State 0 is done
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
            self.states.to_lines(),
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
            if node.id not in self._context.global_vars:
                self.__add_global_var(str(0), node.id)
        else:
            raise TypeError(f"Unsupported lvalue type {type(node)} {pyast.dump(node)}")
        return self.__parse_expression(node)

    def __parse_assign(self, node: pyast.Assign):
        """
        <target0, target1, ...> = <value>;
        """
        assign = ir.NonBlockingSubsitution(
            self.__parse_targets(list(node.targets)),
            self.__parse_expression(node.value),
        )
        return [assign]

    def __parse_statements(
        self, stmts: list[pyast.AST], prefix: str, next_state: ir.State
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
        assert isinstance(next_state, ir.State)

        # state[x] has next state of state[x+1]
        cur_states = [ir.State(f"{prefix}{i}") for i in range(len(stmts))]
        next_states = cur_states[1:] + [next_state]

        for stmt, cur, nextt in zip(stmts, cur_states, next_states):
            self.__parse_statement(stmt, cur, nextt)

        return cur_states[0]

    def __parse_statement(
        self, stmt: pyast.AST, cur_state: ir.State, next_state: ir.State
    ):
        """
        <statement> (e.g. assign, for loop, etc., cannot be equated to)

        creates cur_state
        """
        body = []
        if isinstance(stmt, pyast.Assign):
            body = self.__parse_assign(stmt)
        elif isinstance(stmt, pyast.Yield):
            body = self.__parse_yield(stmt)
        elif isinstance(stmt, pyast.While):
            body = self.__parse_while(stmt, cur_state, next_state)
        elif isinstance(stmt, pyast.If):
            body = self.__parse_ifelse(stmt, cur_state, next_state)
        elif isinstance(stmt, pyast.Expr):
            # TODO: solve the inconsistency
            # raise Exception(f"{pyast.dump(stmt)}")
            self.__parse_statement(stmt.value, cur_state, next_state)
            return
        elif isinstance(stmt, pyast.AugAssign):
            assert isinstance(
                stmt.target, pyast.Name
            ), "Error: only supports single target"
            body = [
                ir.NonBlockingSubsitution(
                    self.__parse_expression(stmt.target),
                    self.__parse_expression(
                        pyast.BinOp(stmt.target, stmt.op, stmt.value)
                    ),
                )
            ]
        else:
            raise TypeError(
                "Error: unexpected statement type", type(stmt), pyast.dump(stmt)
            )

        self.__add_state_var(cur_state)
        self.states.case_items.append(
            ir.CaseItem(
                cur_state,
                [ir.StateSubsitution(self.state_var, next_state), *body],
            )
        )

    def __parse_ifelse(self, stmt: pyast.If, cur_state: ir.State, next_state: ir.State):
        """
        If statement
        """
        assert isinstance(stmt, pyast.If)

        then_start_state = self.__parse_statements(
            list(stmt.body), f"{cur_state.to_string()}then", next_state
        )
        else_start_state = self.__parse_statements(
            list(stmt.orelse), f"{cur_state.to_string()}else", next_state
        )

        ifelse = ir.IfElse(
            self.__parse_expression(stmt.test),
            [ir.StateSubsitution(self.state_var, then_start_state)],
            [ir.StateSubsitution(self.state_var, else_start_state)],
        )

        return [ifelse]

    def __parse_yield(self, node: pyast.Yield):
        """
        Warning: may not work for single output

        Warning: requires self.yieldVars to be complete

        yield <value>;
        """
        if isinstance(node.value, pyast.Tuple):
            output_vars = node.value.elts  # e.g. `yield (1, 2)`
        elif isinstance(node.value, pyast.Constant):
            output_vars = [node.value]  # e.g. `yield 1`
        else:
            raise NotImplementedError(
                f"Unexpected yield {type(node.value)} {pyast.dump(node)}"
            )
        try:
            return [
                ir.NonBlockingSubsitution(
                    ir.Var(self._context.output_vars[idx]),
                    self.__parse_expression(elem),
                )
                for idx, elem in enumerate(output_vars)
            ] + [ir.ValidSubsitution(ir.Var("_valid"), ir.Int(1))]
        except IndexError as err:
            raise IndexError(
                "yield return length differs from function return length type hint"
            ) from err

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

    def __parse_while(
        self, stmt: pyast.While, cur_state: ir.State, next_state: ir.State
    ):
        """
        Converts while loop to a while-true-if-break loop
        """
        assert isinstance(stmt, pyast.While)

        body_start_state = self.__parse_statements(
            list(stmt.body), f"{cur_state.to_string()}while", cur_state
        )

        ifelse = ir.IfElse(
            self.__parse_expression(stmt.test),
            [ir.StateSubsitution(self.state_var, body_start_state)],
            [ir.StateSubsitution(self.state_var, next_state)],
        )

        return [ifelse]
