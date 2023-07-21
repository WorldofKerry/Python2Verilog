"""Parses Python Generator Functions to Intermediate Representation"""

from __future__ import annotations
import copy
import warnings
import ast as pyast
from typing import Optional

from .. import ir
from ..utils.string import Lines, Indent


class GeneratorParser:
    """
    Parses python generator functions to Verilog AST
    """

    def __init__(self, python_func: pyast.FunctionDef):
        """
        Initializes the parser, does quick setup work
        """
        assert isinstance(python_func, pyast.FunctionDef)
        self._name = python_func.name
        self._unique_name_counter = 0
        self._global_vars: dict[str, str] = {}
        self._python_func = python_func

        assert python_func.returns is not None, "Write a return type-hint for function"
        self._output_vars = self.__generate_output_vars(python_func.returns, "")
        self._input_vars = [var.arg for var in self._python_func.args.args]
        self._root = self.__parse_statements(list(python_func.body), "")

    def __str__(self):
        return self.generate_verilog().to_string()

    def get_root(self):
        """
        Gets the root of the IR tree
        """
        return copy.deepcopy(self._root)

    def generate_verilog(self, indent: int = 0):
        """
        Generates the verilog (does the most work, calls other functions)
        """
        stmt_lines = (
            self.__parse_statements(
                list(self._python_func.body),
                prefix="",
                end_stmts=[ir.NonBlockingSubsitution(ir.Var("_done"), ir.Int(1))],
            ).to_lines(),
            Lines(),
        )
        module_lines = self.__stringify_module()
        decl_lines = self.__stringify_declarations(self._global_vars)
        always_blk_lines = self.__stringify_always_block()
        decl_and_always_blk_lines = (
            decl_lines[0].concat(always_blk_lines[0]),
            decl_lines[1].concat(always_blk_lines[1]),
        )  # TODO: there should be a function for this
        init_lines = self.__stringify_initialization(self._global_vars)

        return Lines.nestify(
            [
                module_lines,
                decl_and_always_blk_lines,
                init_lines,
                stmt_lines,
            ],
            indent,
        )

    def parse_statements(
        self,
        stmts: list[pyast.AST],
        prefix: str,
        end_stmts: Optional[list[ir.Statement]] = None,
        reset_to_zero: bool = False,
    ):
        """
        Parses a list of python statements
        """
        return self.__parse_statements(stmts, prefix, end_stmts, reset_to_zero)

    def __parse_statements(
        self,
        stmts: list[pyast.AST],
        prefix: str,
        end_stmts: Optional[list[ir.Statement]] = None,
        reset_to_zero: bool = False,
    ):
        """
        Warning: mutates global_vars

        {
            <statement0>
            <statement1>
            ...
        }
        """
        if not end_stmts:
            end_stmts = []
        assert end_stmts is not None
        state_var = self.__add_global_var(
            str(0), f"{prefix}_STATE{self.__create_unique_name()}"
        )
        cases = []

        index = 0
        for stmt in stmts:
            body = self.__parse_statement(stmt, prefix=state_var)
            case_item = ir.CaseItem(ir.Expression(str(index)), body)
            if (
                not isinstance(stmt, pyast.For)
                and not isinstance(stmt, pyast.While)
                and not isinstance(stmt, pyast.If)
            ):
                case_item.append_end_statements(
                    [
                        ir.StateSubsitution(
                            ir.Var(state_var), ir.Add(ir.Var(state_var), ir.Int(1))
                        )
                    ]
                )
            cases.append(case_item)  # TODO: cases can have multiple statements
            index += 1
        if reset_to_zero:
            end_stmts.append(ir.NonBlockingSubsitution(ir.Var(state_var), ir.Int(0)))

        the_case = ir.Case(ir.Expression(state_var), cases)
        assert end_stmts is not None
        the_case.append_end_statements(end_stmts)

        return ir.Case(ir.Expression(state_var), cases)

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

    def __create_unique_name(self):
        """
        Generates an id that is unique among all unique global variables
        """
        self._unique_name_counter += 1
        return f"{self._unique_name_counter}"

    def __add_global_var(self, initial_value: str, name: str):
        """
        Adds global variables
        """
        self._global_vars[name] = initial_value
        return name

    def get_context(self):
        """
        Gets the context of the Python function
        """
        return ir.Context(
            name=self._name,
            global_vars=copy.deepcopy(self._global_vars),
            input_vars=copy.deepcopy(self._input_vars),
            output_vars=copy.deepcopy(self._output_vars),
        )

    def get_results(self):
        """
        Gets root of IR and Context
        """
        return (self.get_root(), self.get_context())

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
        for var in self._output_vars:
            start_lines += Indent(1) + f"output reg signed [31:0] {var},"
        start_lines += Indent(1) + "output reg _done,"
        start_lines += Indent(1) + "output reg _valid"
        start_lines += ");"
        end_lines += "endmodule"
        return (start_lines, end_lines)

    def __parse_for(self, node: pyast.For, prefix: str):
        """
        Creates a conditional while loop from for loop
        """
        raise NotImplementedError("for not implemented")

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
                [*self._global_vars, *self._output_vars, *self._input_vars]
            ):
                warnings.warn(
                    str(
                        set([*self._global_vars, *self._output_vars, *self._input_vars])
                    )
                )
                self.__add_global_var(str(0), node.value.id)
        elif isinstance(node, pyast.Name):
            if node.id not in self._global_vars:
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

    def __parse_statement(self, stmt: pyast.AST, prefix: str):
        """
        <statement> (e.g. assign, for loop, etc., those that do not return a value)
        """
        if isinstance(stmt, pyast.Assign):
            return self.__parse_assign(stmt)
        if isinstance(stmt, pyast.For):
            return self.__parse_for(stmt, prefix=prefix)
        if isinstance(stmt, pyast.Expr):
            return self.__parse_statement(stmt.value, prefix=prefix)
        if isinstance(stmt, pyast.Yield):
            return self.__parse_yield(stmt)
        if isinstance(stmt, pyast.While):
            return self.__parse_while(stmt, prefix=prefix)
        if isinstance(stmt, pyast.If):
            return self.__parse_ifelse(stmt, prefix=prefix)
        if isinstance(stmt, pyast.AugAssign):
            assert isinstance(
                stmt.target, pyast.Name
            ), "Error: only supports single target"
            return [
                ir.NonBlockingSubsitution(
                    self.__parse_expression(stmt.target),
                    self.__parse_expression(
                        pyast.BinOp(stmt.target, stmt.op, stmt.value)
                    ),
                )
            ]
        raise TypeError(
            "Error: unexpected statement type", type(stmt), pyast.dump(stmt)
        )

    def __parse_ifelse(self, stmt: pyast.If, prefix: str):
        """
        If statement
        """
        assert isinstance(stmt, pyast.If)
        state_var = self.__add_global_var(
            str(0), f"{prefix}_IFELSE{self.__create_unique_name()}"
        )
        conditional_item = ir.CaseItem(
            ir.Int(0),
            [
                ir.IfElse(
                    self.__parse_expression(stmt.test),
                    [ir.NonBlockingSubsitution(ir.Var(state_var), ir.Int(1))],
                    [ir.NonBlockingSubsitution(ir.Var(state_var), ir.Int(2))],
                )
            ],
        )
        then_item = ir.CaseItem(
            ir.Expression("1"),
            [
                self.__parse_statements(
                    list(stmt.body),
                    f"{state_var}",
                    end_stmts=[
                        ir.StateSubsitution(
                            ir.Var(prefix), ir.Add(ir.Var(prefix), ir.Int(1))
                        ),
                        ir.StateSubsitution(ir.Var(state_var), ir.Int(0)),
                    ],
                    reset_to_zero=True,
                )
            ],
        )
        else_item = ir.CaseItem(
            ir.Expression("2"),
            [
                self.__parse_statements(
                    list(stmt.orelse),
                    f"{state_var}",
                    end_stmts=[
                        ir.StateSubsitution(
                            ir.Var(prefix), ir.Add(ir.Var(prefix), ir.Int(1))
                        ),
                        ir.StateSubsitution(ir.Var(state_var), ir.Int(0)),
                    ],
                    reset_to_zero=True,
                )
            ],
        )
        return [
            ir.IfElseWrapper(
                ir.Expression(f"{state_var}"),
                [conditional_item, then_item, else_item],
            )
        ]

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
                    ir.Var(self._output_vars[idx]), self.__parse_expression(elem)
                )
                for idx, elem in enumerate(output_vars)
            ] + [ir.ValidSubsitution(ir.Var("_valid"), ir.Int(1))]
        except IndexError as e:
            raise IndexError(
                "yield return length differs from function return length type hint"
            ) from e

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
                # return vast.Expression(
                #     f"({self.parse_expression(expr.left).to_string()}
                # >> {int(expr.right.value / 2)})"
                # )
                a_var = self.__parse_expression(expr.left).to_string()
                b_var = expr.right.value
                # return vast.Expression(
                #     f"({a} > 0) ? ({a} >> {int(b / 2)}) : -(-({a}) >> {int(b / 2)})"
                # )
                return ir.Expression(
                    f"({a_var} > 0) ? ({a_var} / {b_var}) : ({a_var} / {b_var} - 1)"
                )

            # warnings.warn(pyast.dump(expr))
            # return irast.Expression(
            #     "("
            #     + self.__parse_expression(expr.left).to_string()
            #     + self.__parse_binop(expr)
            #     + self.__parse_expression(expr.right).to_string()
            #     + ")"
            # )
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

    def __parse_while(self, stmt: pyast.While, prefix: str):
        """
        Converts while loop to a while-true-if-break loop
        """
        assert isinstance(stmt, pyast.While)
        assert prefix != ""
        state_var = self.__add_global_var(
            str(0), f"{prefix}_WHILE{self.__create_unique_name()}"
        )
        conditional_item = ir.CaseItem(
            ir.Int(0),
            [
                ir.IfElse(
                    ir.Expression(
                        f"!({self.__parse_expression(stmt.test).to_string()})"
                    ),
                    [
                        ir.StateSubsitution(
                            ir.Var(prefix), ir.Add(ir.Var(prefix), ir.Int(1))
                        )
                    ],
                    [ir.NonBlockingSubsitution(ir.Var(state_var), ir.Int(1))],
                )
            ],
        )
        then_item = ir.CaseItem(
            ir.Expression("1"),
            [
                self.__parse_statements(
                    list(stmt.body),
                    f"{state_var}",
                    end_stmts=[ir.NonBlockingSubsitution(ir.Var(state_var), ir.Int(0))],
                    reset_to_zero=True,
                )
            ],
        )
        return [
            ir.WhileWrapper(
                ir.Expression(f"{state_var}"),
                [conditional_item, then_item],
            )
        ]
