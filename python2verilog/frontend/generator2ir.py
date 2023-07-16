"""Parses Python Generator Functions to Intermediate Representation"""

from __future__ import annotations
import ast as pyast
import warnings
from ..utils.string import Lines, Indent
from .. import ir as vast


class Generator2Ast:
    """
    Parses python generator functions to Verilog AST
    """

    @staticmethod
    def generate_output_vars(node: pyast.AST, prefix: str):
        """
        Generates the yielded variables of the function
        """
        assert isinstance(node, pyast.Subscript)
        assert isinstance(node.slice, pyast.Tuple)
        return [f"{prefix}_out{str(i)}" for i in range(len(node.slice.elts))]

    def create_unique_name(self):
        """
        Generates an id that is unique among all unique global variables
        """
        self.unique_name_counter += 1
        return f"{self.unique_name_counter}"

    def add_global_var(self, initial_value: str, name: str):
        """
        Adds global variables
        """
        self.global_vars[name] = initial_value
        return name

    @staticmethod
    def stringify_always_block():
        """
        always @(posedge _clock) begin
        end
        """
        return (
            Lines(["always @(posedge _clock) begin", Indent(1) + "_valid <= 0;"]),
            Lines(["end"]),
        )

    def __str__(self):
        return self.generate_verilog().to_string()

    def generate_verilog(self, indent: int = 0):
        """
        Generates the verilog (does the most work, calls other functions)
        """
        stmt_lines = (
            self.parse_statements(
                self.root.body,
                prefix="",
                end_stmts=[vast.NonBlockingSubsitution("_done", "1")],
            ).to_lines(),
            Lines(),
        )
        module_lines = self.stringify_module()
        decl_lines = self.stringify_declarations(self.global_vars)
        always_blk_lines = self.stringify_always_block()
        decl_and_always_blk_lines = (
            decl_lines[0].concat(always_blk_lines[0]),
            decl_lines[1].concat(always_blk_lines[1]),
        )  # TODO: there should be a function for this
        init_lines = self.stringify_initialization(self.global_vars)

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
    def stringify_initialization(global_vars: dict[str, str]):
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
    def stringify_declarations(global_vars: dict[str, str]) -> tuple[Lines, Lines]:
        """
        reg [31:0] <name>;
        ...
        """
        return (Lines([f"reg signed [31:0] {v};" for v in global_vars]), Lines())

    def stringify_module(self) -> tuple[Lines, Lines]:
        """
        module <name>(...);

        endmodule
        """
        start_lines, end_lines = Lines(), Lines()
        assert self.name not in {
            "default",
            "module",
            "output",
            "function",
        }  # Verilog Reserved Keywords
        start_lines += f"module {self.name}("
        start_lines += Indent(1) + "input wire _clock,"
        start_lines += Indent(1) + "input wire _start,"
        for var in self.root.args.args:
            start_lines += Indent(1) + f"input wire signed [31:0] {var.arg},"
        for var in self.output_vars:
            start_lines += Indent(1) + f"output reg signed [31:0] {var},"
        start_lines += Indent(1) + "output reg _done,"
        start_lines += Indent(1) + "output reg _valid"
        start_lines += ");"
        end_lines += "endmodule"
        return (start_lines, end_lines)

    def __init__(self, root: pyast.FunctionDef):
        """
        Initializes the parser, does quick setup work
        """
        assert isinstance(root, pyast.FunctionDef)
        self.name = root.name
        self.output_vars = self.generate_output_vars(root.returns, "")
        self.unique_name_counter = 0
        self.global_vars: dict[str, str] = {}
        self.root = root

    def parse_for(self, node: pyast.For, prefix: str = ""):
        """
        Creates a conditional while loop from for loop
        """
        raise NotImplementedError("for")

        def parse_iter(iterator: pyast.AST, node: pyast.AST):
            assert isinstance(iterator, pyast.Call)
            assert iterator.func.id == "range"

            # range(x, y) or range(x)
            if len(iterator.args) == 2:
                start, end = str(iterator.args[0].value), iterator.args[1].id
            else:
                start, end = "0", iterator.args[0].id

            self.add_global_var(
                start, node.target.id
            )  # TODO: not require unique range iterator variables
            return (
                Lines(
                    [
                        f"if ({node.target.id} >= {end}) begin // FOR LOOP START",
                        Indent(1) + f"{prefix}_STATE = {prefix}_STATE + 1;",
                        Indent(1) + f"{node.target.id} <= 0;",
                        "end else begin // FOR LOOP BODY",
                    ]
                ),
                Lines(["end // FOR LOOP END"]),
            )

        conditional_lines = parse_iter(node.iter, node)
        stmt_lines = self.parse_statements(
            node.body,
            f"{prefix}_BODY_{self.create_unique_name()}",
            end_stmts=Lines([f"{node.target.id} <= {node.target.id} + 1;"]),
            reset_to_zero=True,
        )
        return Lines.nestify([conditional_lines, stmt_lines])

    def parse_targets(self, nodes: list[pyast.AST]):
        """
        Warning: only single target on left-hand-side supported

        <target0, target1, ...> =
        """
        buffer = ""
        assert len(nodes) == 1
        node = nodes[0]
        assert isinstance(node, pyast.Name)
        if node.id not in self.global_vars:
            self.add_global_var(0, node.id)
        buffer += self.parse_expression(node).to_string()
        return buffer

    def parse_assign(self, node: pyast.Assign):
        """
        <target0, target1, ...> = <value>;
        """
        assign = vast.NonBlockingSubsitution(
            self.parse_targets(node.targets),
            self.parse_expression(node.value).to_string(),
        )
        return [assign]

    def parse_statement(self, stmt: pyast.AST, prefix: str = ""):
        """
        <statement> (e.g. assign, for loop, etc., those that do not return a value)
        """
        if isinstance(stmt, pyast.Assign):
            return self.parse_assign(stmt)
        if isinstance(stmt, pyast.For):
            return self.parse_for(stmt, prefix=prefix)
        if isinstance(stmt, pyast.Expr):
            return self.parse_statement(stmt.value, prefix=prefix)
        if isinstance(stmt, pyast.Yield):
            return self.parse_yield(stmt)
        if isinstance(stmt, pyast.While):
            return self.parse_while(stmt, prefix=prefix)
        if isinstance(stmt, pyast.If):
            return self.parse_if(stmt, prefix=prefix)
        if isinstance(stmt, pyast.AugAssign):
            assert isinstance(
                stmt.target, pyast.Name
            ), "Error: only supports single target"
            return [
                vast.NonBlockingSubsitution(
                    self.parse_expression(stmt.target).to_string(),
                    self.parse_expression(
                        pyast.BinOp(stmt.target, stmt.op, stmt.value)
                    ).to_string(),
                )
            ]
        raise TypeError(
            "Error: unexpected statement type", type(stmt), pyast.dump(stmt)
        )

    def parse_if(self, stmt: pyast.If, prefix: str = ""):
        """
        If statement
        """
        assert isinstance(stmt, pyast.If)
        state_var = self.add_global_var("0", f"{prefix}_IF")
        conditional_item = vast.CaseItem(
            vast.Expression("0"),
            [
                vast.Statement(f"if ({self.parse_expression(stmt.test).to_string()})"),
                vast.NonBlockingSubsitution(state_var, "1"),
                vast.Statement(
                    "else "
                    + vast.NonBlockingSubsitution(state_var, "2").to_string().strip()
                ),  # TODO: cleanup
            ],
        )
        then_item = vast.CaseItem(
            vast.Expression("1"),
            [
                self.parse_statements(
                    stmt.body,
                    f"{state_var}{self.create_unique_name()}",
                    end_stmts=[
                        vast.NonBlockingSubsitution(
                            f"{prefix}_STATE", f"{prefix}_STATE + 1"
                        ),
                        vast.NonBlockingSubsitution(state_var, "0"),
                    ],
                    reset_to_zero=True,
                )
            ],
        )
        else_item = vast.CaseItem(
            vast.Expression("2"),
            [
                self.parse_statements(
                    stmt.orelse,
                    f"{state_var}{self.create_unique_name()}",
                    end_stmts=[
                        vast.NonBlockingSubsitution(
                            f"{prefix}_STATE", f"{prefix}_STATE + 1"
                        ),
                        vast.NonBlockingSubsitution(state_var, "0"),
                    ],
                    reset_to_zero=True,
                )
            ],
        )
        return [
            vast.Case(
                vast.Expression(f"{state_var}"),
                [conditional_item, then_item, else_item],
            )
        ]

    def parse_statements(
        self,
        stmts: list[pyast.AST],
        prefix: str,
        end_stmts: list[vast.Statement] = None,
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
            end_stmts = Lines()
        state_var = self.add_global_var("0", f"{prefix}_STATE")
        cases = []

        index = 0
        for stmt in stmts:
            a_output = self.parse_statement(stmt, prefix=prefix)
            assert isinstance(a_output, list)
            body = self.parse_statement(stmt, prefix=prefix)
            case_item = vast.CaseItem(vast.Expression(str(index)), body)
            if (
                not isinstance(stmt, pyast.For)
                and not isinstance(stmt, pyast.While)
                and not isinstance(stmt, pyast.If)
            ):
                case_item.append_end_statements(
                    [vast.NonBlockingSubsitution(state_var, f"{state_var} + 1")]
                )
            cases.append(case_item)  # TODO: cases can have multiple statements
            index += 1
        # end_stmts = [vast.Statement(stmt) for stmt in end_stmts]
        for stmt in end_stmts:
            assert isinstance(stmt, vast.Statement)
        if reset_to_zero:
            end_stmts.append(vast.NonBlockingSubsitution(state_var, "0"))

        the_case = vast.Case(vast.Expression(state_var), cases)
        the_case.append_end_statements(end_stmts)

        return vast.Case(vast.Expression(state_var), cases)

    def parse_yield(self, node: pyast.Yield):
        """
        Warning: may not work for single output

        Warning: requires self.yieldVars to be complete

        yield <value>;
        """
        assert isinstance(node.value, pyast.Tuple)
        return [
            vast.NonBlockingSubsitution(
                self.output_vars[idx], self.parse_expression(elem).to_string()
            )
            for idx, elem in enumerate(node.value.elts)
        ] + [vast.NonBlockingSubsitution("_valid", "1")]

    @staticmethod
    def parse_binop(node: pyast.BinOp):
        """
        <left> <op> <right>
        """
        if isinstance(node.op, pyast.Add):
            return " + "
        if isinstance(node.op, pyast.Sub):
            return " - "
        if isinstance(node.op, pyast.Mult):
            return " * "
        if isinstance(node.op, pyast.Div):
            warnings.warn("Warning: division treated as floor division")
            return " / "
        if isinstance(node.op, pyast.FloorDiv):
            return " / "
        raise TypeError(
            "Error: unexpected binop type", type(node.op), pyast.dump(node.op)
        )

    def parse_expression(self, expr: pyast.AST):
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        if isinstance(expr, pyast.Constant):
            return vast.Expression(str(expr.value))
        if isinstance(expr, pyast.Name):
            return vast.Expression(expr.id)
        if isinstance(expr, pyast.Subscript):
            return self.parse_subscript(expr)
        if isinstance(expr, pyast.BinOp):
            return vast.Expression(
                "("
                + self.parse_expression(expr.left).to_string()
                + self.parse_binop(expr)
                + self.parse_expression(expr.right).to_string()
                + ")"
            )
        if isinstance(expr, pyast.UnaryOp):
            if isinstance(expr.op, pyast.USub):
                return vast.Expression(
                    f"-({self.parse_expression(expr.operand).to_string()})"
                )
            raise TypeError(
                "Error: unexpected unaryop type", type(expr.op), pyast.dump(expr.op)
            )
        if isinstance(expr, pyast.Compare):
            return self.parse_compare(expr)
        raise TypeError(
            "Error: unexpected expression type", type(expr), pyast.dump(expr)
        )

    def parse_subscript(self, node: pyast.Subscript):
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return vast.Expression(
            f"{self.parse_expression(node.value)}[{self.parse_expression(node.slice)}]"
        )

    def parse_compare(self, node: pyast.Compare):
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
        return vast.Expression(
            f"{self.parse_expression(node.left).to_string()} {operator}"
            f" {self.parse_expression(node.comparators[0]).to_string()}"
        )

    def parse_while(self, stmt: pyast.While, prefix: str = ""):
        """
        Converts while loop to a while-true-if-break loop
        """
        assert isinstance(stmt, pyast.While)
        state_var = self.add_global_var("0", f"{prefix}_WHILE")
        conditional_item = vast.CaseItem(
            vast.Expression("0"),
            [
                vast.IfElse(
                    vast.Expression(
                        f"!({self.parse_expression(stmt.test).to_string()})"
                    ),
                    [
                        vast.NonBlockingSubsitution(
                            f"{prefix}_STATE", f"{prefix}_STATE + 1"
                        )
                    ],
                    [vast.NonBlockingSubsitution(state_var, "1")],
                )
            ],
        )
        then_item = vast.CaseItem(
            vast.Expression("1"),
            [
                self.parse_statements(
                    stmt.body,
                    f"{state_var}{self.create_unique_name()}",
                    end_stmts=[vast.NonBlockingSubsitution(f"{state_var}", "0")],
                    reset_to_zero=True,
                )
            ],
        )
        return [
            vast.While(
                vast.Expression(f"{state_var}"),
                [conditional_item, then_item],
            )
        ]
