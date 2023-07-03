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
        bodyBuffers = self.parse_statements(
            self.root.body, indent + 3, f"", endStatements="_done = 1;\n"
        )  # TODO: remove 'arbitrary' + 3
        moduleBuffers = self.stringify_module()
        declBuffers = self.stringify_declarations(self.global_vars)
        alwaysBuffers = self.stringify_always_block()
        initBuffers = self.stringify_init(self.global_vars)

        return Lines.nestify(
            [
                moduleBuffers,
                declBuffers,
                alwaysBuffers,
                initBuffers,
                bodyBuffers,
            ],
            indent,
        )

    @staticmethod
    def stringify_init(global_vars: dict[str, str]):
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

    def parse_for(self, node: ast.For, indent: int = 0, prefix: str = ""):
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
                        f"if ({node.target.id} >= {end}) {prefix}_STATE = {prefix}_STATE + 1; // FOR LOOP START",
                        "else begin",
                    ]
                ),
                Lines(["end // FOR LOOP END"]),
            )

        conditionalBuffer = parse_iter(node.iter, node)
        statementsBuffer = self.parse_statements(
            node.body,
            indent + 1,
            f"{prefix}_INNER_{self.create_unique_name()}",
            endStatements=f"{node.target.id} <= {node.target.id} + 1'",
            resetToZero=True,
        )
        nestedLines = NestedLines([conditionalBuffer, statementsBuffer])
        print("=====a\n" + str(nestedLines.toLines(indent)) + "\n=====a\n")
        return nestedLines.toLines(indent)

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

    def parse_statement(self, stmt: ast.AST, indent: int, prefix: str = ""):
        """
        <statement> (e.g. assign, for loop, etc., those that do not return a value)
        """
        match type(stmt):
            case ast.Assign:
                return Lines([self.parse_assign(stmt, indent)])
            case ast.For:
                return self.parse_for(stmt, indent, prefix)
            case ast.Expr:
                return self.parse_statement(stmt.value, indent)
            case ast.Yield:
                return Lines([self.parse_yield(stmt, indent, prefix)])
            case _:
                raise Exception("Error: unexpected statement type", type(stmt))

    def parse_statements(
        self,
        stmts: list[ast.AST],
        indent: int,
        prefix: str,
        endStatements: str = "",
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
        lines += f"case ({state_var})"
        state_counter = 0
        for stmt in stmts:
            state = self.add_global_var(
                str(state_counter), f"{prefix}_STATE_{state_counter}"
            )
            state_counter += 1

            # buffer += indentify(indent + 1, f"{state}: begin\n")
            lines += IStr(f"{state}: begin") >> 1
            for line in self.parse_statement(stmt, indent + 2, prefix):
                lines += line
                print("=====b\n" + str(line) + "\n=====b\n")
            if type(stmt) != ast.For:
                # Non-for-loop state machines always continue to next state after running current state's case statement
                # TODO: figure out better way to handle this, perhaps add to end statements of caller
                lines += IStr(f"{state_var} <= {state_var} + 1;") >> 2
            lines += IStr(f"end") >> 1
        del lines[-1]  # TODO: check this actually works

        if resetToZero:  # TODO: think about what default should be
            lines += IStr(f"{state_var} <= 0;") >> 2

        if endStatements != "":
            lines += IStr(endStatements) >> 2
        lines += IStr(f"end") >> 1

        lines += IStr(f"endcase")
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

    def parse_binop(self, node: ast.BinOp):
        """
        <left> <op> <right>
        """
        match type(node.op):
            case ast.Add:
                return " + "
            case ast.Sub:
                return " - "
            case _:
                print("Error: unexpected binop type", type(node.op))

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
                print("Error: unexpected expression type", type(expr))
                return ""

    def parse_subscript(self, node: ast.Subscript, indent: int = 0):
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return f"{self.parse_expression(node.value, indent)}[{self.parse_expression(node.slice, indent)}]"
