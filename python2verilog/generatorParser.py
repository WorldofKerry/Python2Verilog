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
        startLines += indentify(1, "_done <= 0;")
        for v in global_vars:
            startLines += indentify(1, f"{v} <= {global_vars[v]};")
        startLines += f"end else begin"
        endLines += "end"
        return (startLines, endLines)

    @staticmethod
    def stringify_declarations(global_vars: dict[str, str]) -> tuple[Lines, Lines]:
        """
        reg [31:0] <name>;
        ...
        """
        return (Lines([f"reg [31:0] {v};" for v in global_vars]), Lines())

    def stringify_module(self) -> tuple[Lines, Lines]:
        """
        module <name>(...);

        endmodule
        """
        startLines, endLines = Lines(), Lines()
        startLines += f"module {self.name}("
        startLines += indentify(1, "input wire _clock,")
        startLines += indentify(1, "input wire _start,")
        for var in self.root.args.args:
            startLines += indentify(1, f"input wire [31:0] {var.arg},")
        for var in self.yieldVars:
            startLines += indentify(1, f"output reg [31:0] {var},")
        startLines += indentify(1, "output reg _done,\n")
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
                        IStr(f"{prefix}_STATE = {prefix}_STATE + 1;") >> 1,
                        IStr(f"{node.target.id} <= 0;") >> 1,
                        "end else begin // FOR LOOP BODY",
                    ]
                ),
                Lines(["end // FOR LOOP END"]),
            )

        conditionalBuffer = parse_iter(node.iter, node)
        statementsBuffer = self.parse_statements(
            node.body,
            f"{prefix}_INNER_{self.create_unique_name()}",
            endStatements=Lines([f"{node.target.id} <= {node.target.id} + 1;"]),
            resetToZero=True,
        )
        return Lines.nestify([conditionalBuffer, statementsBuffer])

    @staticmethod
    def parse_targets(nodes: list[ast.AST]):
        """
        Warning: only single target on left-hand-side supported

        <target0, target1, ...> =
        """
        buffer = ""
        assert len(nodes) == 1
        for node in nodes:
            buffer += GeneratorParser.parse_expression(node)
        return buffer

    @staticmethod
    def parse_assign(node: ast.Assign):
        """
        <target0, target1, ...> = <value>;
        """
        return f"{GeneratorParser.parse_targets(node.targets)} = {GeneratorParser.parse_expression(node.value)};\n"

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
            case _:
                raise Exception("Error: unexpected statement type", type(stmt))

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

            lines += IStr(f"{state}: begin") >> 1

            for line in self.parse_statement(stmt, prefix=prefix) >> 2:
                lines += line
                assert str(line).find("\n") == -1
            if type(stmt) != ast.For:
                # Non-for-loop state machines always continue to next state after running current state's case statement
                # TODO: figure out better way to handle this, perhaps add to end statements of caller
                lines += IStr(f"{state_var} <= {state_var} + 1;") >> 2
            lines += IStr(f"end") >> 1
            prevI = i

        assert isinstance(endStatements, Lines)
        # TODO: cleanup, remove the above enumerate?
        i = prevI + 1
        for stmt in endStatements:
            state = self.add_global_var(str(i), f"{prefix}_STATE_{i}")

            lines += IStr(f"{state}: begin // END STATEMENTS STATE") >> 1
            # print("DEBUG stmt:" + str(stmt))
            lines += IStr(stmt) >> 2
            # print("DEBUG0:" + lines.toString())
            lines += IStr(f"end") >> 1
            i += 1

        del lines[-1]

        if resetToZero:  # TODO: think about what default should be
            lines += IStr(f"{state_var} <= 0; // LOOP FOR LOOP STATEMENTS") >> 2

        lines += IStr(f"end") >> 1

        lines += IStr(f"endcase // STATEMENTS END")
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
            lines += f"{self.yieldVars[i]} <= {GeneratorParser.parse_expression(e)};"
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
            case _:
                raise Exception("Error: unexpected binop type", type(node.op))

    @staticmethod
    def parse_expression(expr: ast.AST, indent: int = 0):
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        match type(expr):
            case ast.Constant:
                return str(expr.value)
            case ast.Name:
                return expr.id
            case ast.Subscript:
                return GeneratorParser.parse_subscript(expr, indent)
            case ast.BinOp:
                return (
                    GeneratorParser.parse_expression(expr.left)
                    + GeneratorParser.parse_binop(expr)
                    + GeneratorParser.parse_expression(expr.right)
                )
            case _:
                raise Exception("Error: unexpected expression type", type(expr))

    def parse_subscript(self, node: ast.Subscript, indent: int = 0):
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return f"{self.parse_expression(node.value, indent)}[{self.parse_expression(node.slice, indent)}]"

    def parse_for_new(self, node: ast.For, prefix: str = ""):
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
