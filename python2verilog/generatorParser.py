from __future__ import annotations
import ast
from .utils import *


class GeneratorParser:
    """
    Parses python generator functions
    """

    @staticmethod
    def generate_return_vars(node: ast.AST, prefix: str):
        """
        Generates the yielded variables of the function
        """
        assert type(node) == ast.Subscript
        assert type(node.slice) == ast.Tuple
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
        return (Lines(["always @(posedge _clock) begin"]), Lines(["end"]))

    def generate_verilog(self, indent: int = 0):
        """
        Generates the verilog (does the most work, calls other functions)
        """
        stmntLines = self.parse_statements(
            self.root.body, prefix="", endStatements=Lines(["_done = 1;"])
        )
        bufferLines = self.stringify_module()
        declarationLines = self.stringify_declarations(self.global_vars)
        alwaysBlockLines = self.stringify_always_block()
        initializationLines = self.stringify_initialization(self.global_vars)

        return Lines.nestify(
            [
                bufferLines,
                declarationLines,
                alwaysBlockLines,
                initializationLines,
                stmntLines,
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
        startLines, endLines = Lines(), Lines()
        startLines += f"if (_start) begin"
        startLines += Indent(1) + "_done <= 0;"
        for v in global_vars:
            startLines += Indent(1) + f"{v} <= {global_vars[v]};"
        startLines += f"end else begin"
        endLines += "end"
        return (startLines, endLines)

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
        startLines, endLines = Lines(), Lines()
        startLines += f"module {self.name}("
        startLines += Indent(1) + "input wire _clock,"
        startLines += Indent(1) + "input wire _start,"
        for var in self.root.args.args:
            startLines += Indent(1) + f"input wire signed [31:0] {var.arg},"
        for var in self.yieldVars:
            startLines += Indent(1) + f"output reg signed [31:0] {var},"
        startLines += Indent(1) + "output reg _done,\n"
        startLines[-1] = startLines[-1].removesuffix(",\n") + "\n);"
        endLines += "endmodule"
        return (startLines, endLines)

    def __init__(self, root: ast.FunctionDef):
        """
        Initializes the parser, does quick setup work
        """
        self.name = root.name
        self.yieldVars = self.generate_return_vars(root.returns, f"")
        self.unique_name_counter = 0
        self.global_vars: dict[str, str] = {}
        self.root = root

    def parse_for(self, node: ast.For, prefix: str = ""):
        """
        Creates a conditional while loop from for loop
        """

        def parse_iter(iter: ast.AST, node: ast.AST):
            assert type(iter) == ast.Call
            assert iter.func.id == "range"

            # range(x, y) or range(x)
            if len(iter.args) == 2:
                start, end = str(iter.args[0].value), iter.args[1].id
            else:
                start, end = "0", iter.args[0].id

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

        conditionalBuffer = parse_iter(node.iter, node)
        statementsBuffer = self.parse_statements(
            node.body,
            f"{prefix}_BODY_{self.create_unique_name()}",
            endStatements=Lines([f"{node.target.id} <= {node.target.id} + 1;"]),
            resetToZero=True,
        )
        return Lines.nestify([conditionalBuffer, statementsBuffer])

    def parse_targets(self, nodes: list[ast.AST]):
        """
        Warning: only single target on left-hand-side supported

        <target0, target1, ...> =
        """
        buffer = ""
        assert len(nodes) == 1
        for node in nodes:
            assert type(node) == ast.Name
            if node.id not in self.global_vars:
                self.add_global_var(0, node.id)
            buffer += self.parse_expression(node)
        return buffer

    def parse_assign(self, node: ast.Assign):
        """
        <target0, target1, ...> = <value>;
        """
        return f"{self.parse_targets(node.targets)} <= {self.parse_expression(node.value)};"

    def parse_statement(self, stmt: ast.AST, prefix: str = ""):
        """
        <statement> (e.g. assign, for loop, etc., those that do not return a value)
        """
        match type(stmt):
            case ast.Assign:
                return Lines([self.parse_assign(stmt)])
            case ast.For:
                return self.parse_for(stmt, prefix=prefix)
            case ast.Expr:
                return self.parse_statement(stmt.value, prefix=prefix)
            case ast.Yield:
                return self.parse_yield(stmt)
            case ast.While:
                return self.parse_while(stmt, prefix=prefix)
            case ast.If:
                return self.parse_if(stmt, prefix=prefix)
            case _:
                raise Exception(
                    "Error: unexpected statement type", type(stmt), ast.dump(stmt)
                )

    def parse_if(self, stmt: ast.If, prefix: str = ""):
        """
        If statement
        """
        assert len(stmt.orelse) >= 1  # Currently only supports if-else
        if_conditional = (
            Lines(
                [
                    f"if ({self.parse_expression(stmt.test)}) begin // IF STATEMENT START",
                ]
            ),
            Lines([f"end else begin"]),
        )
        then_body = self.parse_statements(
            stmt.body, f"{prefix}_THEN_{self.create_unique_name()}", 
            endStatements=Lines([f"{prefix}_STATE <= {prefix}_STATE + 1; // FROM IF"]),
            resetToZero=True
        )
        if_then = Lines.nestify([if_conditional, then_body])

        if_then_skip_end = (if_then, Lines([f"end // IF STATEMENT END"]))

        else_body = self.parse_statements(
            stmt.orelse, f"{prefix}_ELSE_{self.create_unique_name()}",
            endStatements=Lines([f"{prefix}_STATE <= {prefix}_STATE + 1; // FROM IF"]),
            resetToZero=True
        )
        return Lines.nestify([if_then_skip_end, else_body])

    def parse_statements(
        self,
        stmts: list[ast.AST],
        prefix: str,
        endStatements: Lines = Lines(),
        resetToZero: bool = False,
    ):
        """
        Warning: mutates global_vars
        {
            <statement0>
            <statement1>
            ...
        }
        """
        state_var = self.add_global_var("0", f"{prefix}_STATE")
        lines = Lines()
        lines += f"case ({state_var}) // STATEMENTS START"
        prevI = 0

        for i, stmt in enumerate(stmts):
            state = self.add_global_var(str(i), f"{prefix}_STATE_{i}")

            lines += Indent(1) + f"{state}: begin"

            for line in self.parse_statement(stmt, prefix=prefix) >> 2:
                lines += line
                assert str(line).find("\n") == -1
            if type(stmt) != ast.For and type(stmt) != ast.While and type(stmt) != ast.If:
                # Non-for-loop state machines always continue to next state after running current state's case statement
                # TODO: figure out better way to handle this, perhaps add to end statements of caller
                lines += (
                    Indent(2) + f"{state_var} <= {state_var} + 1; // INCREMENT STATE"
                )
            lines += Indent(1) + f"end"
            prevI = i

        assert isinstance(endStatements, Lines)
        # TODO: cleanup, remove the above enumerate?
        i = prevI + 1
        for stmt in endStatements:
            state = self.add_global_var(str(i), f"{prefix}_STATE_{i}")

            lines += Indent(1) + f"{state}: begin // END STATEMENTS STATE"
            lines += Indent(2) + stmt
            lines += Indent(1) + f"end"
            i += 1

        del lines[-1]

        if resetToZero:  # TODO: think about what default should be
            lines += Indent(2) + f"{state_var} <= 0; // LOOP FOR LOOP STATEMENTS"

        lines += Indent(1) + f"end"

        lines += f"endcase // STATEMENTS END"
        return (lines, Lines())  # TODO: cleanup

    def parse_yield(self, node: ast.Yield):
        """
        Warning: may not work for single output

        Warning: requires self.yieldVars to be complete

        yield <value>;
        """
        assert type(node.value) == ast.Tuple
        lines = Lines()
        for i, e in enumerate(node.value.elts):
            lines += f"{self.yieldVars[i]} <= {self.parse_expression(e)};"
        return lines

    @staticmethod
    def parse_binop(node: ast.BinOp):
        """
        <left> <op> <right>
        """
        match type(node.op):
            case ast.Add:
                return " + "
            case ast.Sub:
                return " - "
            case ast.Mult:
                return " * "
            case ast.Div:
                return " / "
            case _:
                raise Exception(
                    "Error: unexpected binop type", type(node.op), ast.dump(node.op)
                )

    def parse_expression(self, expr: ast.AST):
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        match type(expr):
            case ast.Constant:
                return str(expr.value)
            case ast.Name:
                return expr.id
            case ast.Subscript:
                return self.parse_subscript(expr)
            case ast.BinOp:
                return (
                    self.parse_expression(expr.left)
                    + self.parse_binop(expr)
                    + self.parse_expression(expr.right)
                )
            case ast.Compare:
                return self.parse_compare(expr)
            case _:
                raise Exception("Error: unexpected expression type", type(expr))

    def parse_subscript(self, node: ast.Subscript):
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return (
            f"{self.parse_expression(node.value)}[{self.parse_expression(node.slice)}]"
        )

    def parse_compare(self, node: ast.Compare):
        """
        <left> <op> <comparators>
        """
        assert len(node.ops) == 1
        assert len(node.comparators) == 1

        match type(node.ops[0]):
            case ast.Lt:
                operator = "<"
            case ast.LtE:
                operator = "<="
            case ast.Gt:
                operator = ">"
            case ast.GtE:
                operator = ">="
            case _:
                raise Exception(
                    "Error: unknown operator", type(node.ops[0]), ast.dump(node.ops[0])
                )
        return f"{self.parse_expression(node.left)} {operator} {self.parse_expression(node.comparators[0])}"

    def parse_while(self, node: ast.While, prefix: str = ""):
        """
        Converts while loop to a while-true-if-break loop
        """
        conditional = (
            Lines(
                [
                    f"if (!({self.parse_expression(node.test)})) begin // WHILE LOOP START",
                    Indent(1) + f"{prefix}_STATE = {prefix}_STATE + 1;",
                    f"end else begin",
                ]
            ),
            Lines([f"end // WHILE LOOP END"]),
        )

        statements = self.parse_statements(
            node.body, f"{prefix}_BODY_{self.create_unique_name()}", resetToZero=True
        )

        return Lines.nestify([conditional, statements])
