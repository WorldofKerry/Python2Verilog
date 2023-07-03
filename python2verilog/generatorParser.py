import ast
from .utils import *


class GeneratorParser:
    """
    Parses python generator functions
    """

    def generate_return_vars(self, node: ast.AST, prefix: str) -> str:
        """
        Generates the yielded variables of the function
        """
        assert type(node) == ast.Subscript
        assert type(node.slice) == ast.Tuple
        return [f"{prefix}_out{str(i)}" for i in range(len(node.slice.elts))]

    def get_unique_name(self) -> str:
        """
        Generates an id that is unique among all unique global variables
        """
        self.unique_name_counter += 1
        return f"{self.unique_name_counter}"

    def add_unique_global_var(self, initial_value: str, name_prefix: str = "") -> None:
        """
        Adds unique global var to global variables
        """
        name = f"{name_prefix}_{self.get_unique_name()}"
        self.add_global_var(initial_value, name)
        return name

    def add_global_var(self, initial_value: str, name: str) -> None:
        """
        Adds global variables
        """
        self.global_vars[name] = initial_value
        return name

    def stringify_var_declaration(self) -> list[Lines]:
        """
        reg [31:0] <name>
        Warning: requires self.global_vars to be complete
        """
        buffers = Lines()
        for var in self.global_vars:
            buffers += f"reg [31:0] {var}"
        return buffers

    def stringify_always_block(self) -> tuple[Lines, Lines]:
        """
        always @(posedge _clock) begin
        end
        """
        return [Lines(["always @(posedge _clock) begin"]), Lines(["end"])]

    def generate_verilog(self, indent: int = 0) -> str:
        """
        Generates the verilog (does the most work, calls other functions)
        """
        bodyBuffers = self.parse_statements(
            self.root.body, indent + 3, f"", endStatements="_done = 1;\n"
        )  # TODO: remove 'arbitrary' + 3
        moduleBuffers = self.stringify_module()
        declBuffers = self.stringify_declarations()
        alwaysBuffers = self.stringify_always_block()
        initBuffers = self.stringify_init()
        # print("==========s")
        # print(initBuffers[0])
        # print("=========e")

        # print(bodyBuffers)
        # print("========f")

        buffers = NestedLines(
            [
                moduleBuffers,
                declBuffers,
                alwaysBuffers,
                initBuffers,
                bodyBuffers,
            ]
        )
        self.buffer = buffers.toString(indent)

        return self.buffer

    def stringify_init(self) -> tuple[Lines, Lines]:
        """
        if (_start) begin
            <var> = <value>;
            ...
        end else begin
        ...
        end
        """
        startBuffers = Lines()
        endBuffers = Lines()
        # print("==========s")
        # print(startBuffers, endBuffers)
        # print("=========e")
        startBuffers += f"if (_start) begin"
        startBuffers += indentify(1, "_done <= 0;")
        for v in self.global_vars:
            startBuffers += indentify(1, f"{v} <= {self.global_vars[v]};")
        startBuffers += f"end else begin"
        endBuffers += "end"
        return [startBuffers, endBuffers]

    def stringify_declarations(self) -> tuple[Lines, Lines]:
        """
        reg [31:0] <name>;
        ...
        """
        return [Lines([f"reg [31:0] {v};" for v in self.global_vars]), Lines()]

    def stringify_module(self) -> tuple[Lines, Lines]:
        """
        module <name>(...);
        endmodule
        """
        startBuffers = Lines()
        endBuffers = Lines()
        startBuffers += f"module {self.name}("
        startBuffers += indentify(1, "input wire _clock,")
        startBuffers += indentify(1, "input wire _start,")
        for var in self.root.args.args:
            startBuffers += indentify(1, f"input wire [31:0] {var.arg},")
        for var in self.yieldVars:
            startBuffers += indentify(1, f"output reg [31:0] {var},")
        startBuffers += indentify(1, "output reg _done,\n")
        startBuffers[-1] = startBuffers[-1].removesuffix(",\n") + "\n);"
        endBuffers += "endmodule"
        return [startBuffers, endBuffers]

    def __init__(self, root: ast.FunctionDef):
        """
        Initializes the parser, does quick setup work
        """
        self.name = root.name
        self.yieldVars = self.generate_return_vars(root.returns, f"")
        self.unique_name_counter = 0
        self.global_vars: dict[str, str] = {}
        self.root = root

    def parse_for(self, node: ast.For, indent: int = 0, prefix: str = "") -> str:
        """
        Creates a conditional while loop from for loop
        """

        def parse_iter(iter: ast.AST, node: ast.AST) -> tuple[list[str], list[str]]:
            assert type(iter) == ast.Call
            assert iter.func.id == "range"
            if len(iter.args) == 2:
                start, end = str(iter.args[0].value), iter.args[1].id
            else:
                start, end = "0", iter.args[0].id
            self.add_global_var(start, node.target.id)
            return [
                Lines(
                    [
                        f"if ({node.target.id} >= {end}) {prefix}_STATE = {prefix}_STATE + 1; // FOR LOOP START",
                        "else begin",
                    ]
                ),
                Lines(["end // FOR LOOP END"]),
            ]
        conditionalBuffer = parse_iter(node.iter, node)
        statementsBuffer = self.parse_statements(
            node.body,
            indent + 1,
            f"{prefix}_INNER_{self.get_unique_name()}",
            endStatements=f"{node.target.id} <= {node.target.id} + 1'",
            resetToZero=True,
        )
        nestedLines = NestedLines(
            [
                conditionalBuffer, 
                statementsBuffer
            ]
        )
        print("=====a\n" + str(nestedLines.toLines(indent)) + "\n=====a\n")
        return nestedLines.toLines(indent)

    def parse_targets(self, nodes: list[ast.AST], indent: int = 0) -> str:
        """
        <target0, target1, ...> = <value>;
        """
        buffer = ""
        assert len(nodes) == 1
        for node in nodes:
            buffer += self.parse_expression(node, indent)
        return buffer

    def parse_assign(self, node: ast.Assign, indent: int = 0) -> str:
        """
        <target0, target1, ...> = <value>;
        """
        buffer = indentify(indent)
        buffer += self.parse_targets(node.targets, indent)
        buffer += " = "
        buffer += self.parse_expression(node.value, indent)
        buffer += "\n"
        return buffer

    def parse_statement(self, stmt: ast.AST, indent: int, prefix: str = "") -> Lines:
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
                print("Error: unexpected statement type", type(stmt))
                return ""

    def parse_statements(
        self,
        stmts: list[ast.AST],
        indent: int,
        prefix: str,
        endStatements: str = "",
        resetToZero: bool = False,
    ) -> tuple[Lines, Lines]:
        """
        {
            <statement0>
            <statement1>
            ...
        }
        """
        state_var = self.add_global_var("0", f"{prefix}_STATE")
        buffer = Lines()
        buffer += f"case ({state_var})"
        state_counter = 0
        for stmt in stmts:
            state = self.add_global_var(
                str(state_counter), f"{prefix}_STATE_{state_counter}"
            )
            state_counter += 1

            # buffer += indentify(indent + 1, f"{state}: begin\n")
            buffer += IStr(f"{state}: begin") >> 1            
            for line in self.parse_statement(stmt, indent + 2, prefix): 
                buffer += line                
                print("=====b\n" + str(line) + "\n=====b\n")
            if type(stmt) != ast.For:
                # Non-for-loop state machines always continue to next state after running current state's case statement
                # TODO: figure out better way to handle this, perhaps add to end statements of caller
                buffer += IStr(f"{state_var} <= {state_var} + 1;") >> 2
            buffer += IStr(f"end") >> 1
        del buffer[-1]  # TODO: check this actually works

        if resetToZero:  # TODO: think about what default should be
            buffer += IStr(f"{state_var} <= 0;") >> 2

        if endStatements != "":
            buffer += IStr(endStatements) >> 2
        buffer += IStr(f"end") >> 1

        buffer += IStr(f"endcase")
        return [buffer, Lines()]  # TODO: cleanup

    def parse_yield(self, node: ast.Yield, indent: int, prefix: str) -> str:
        """
        yield <value>;
        """
        assert type(node.value) == ast.Tuple
        buffer = ""
        for i, e in enumerate(node.value.elts):
            buffer += indentify(
                indent,
                f"{self.yieldVars[i]} <= {self.parse_expression(e, indent)};\n",
            )
        return buffer

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

    def parse_expression(self, expr: ast.AST, indent: int = 0) -> str:
        """
        <expression> (e.g. constant, name, subscript, etc., those that return a value)
        """
        match type(expr):
            case ast.Constant:
                return str(expr.value)
            case ast.Name:
                return expr.id
            case ast.Subscript:
                return self.parse_subscript(expr, indent)
            case ast.BinOp:
                return (
                    self.parse_expression(expr.left)
                    + self.parse_binop(expr)
                    + self.parse_expression(expr.right)
                )
            case _:
                print("Error: unexpected expression type", type(expr))
                return ""

    def parse_subscript(self, node: ast.Subscript, indent: int = 0) -> str:
        """
        <value>[<slice>]
        Note: built from right to left, e.g. [z] -> [y][z] -> [x][y][z] -> matrix[x][y][z]
        """
        return f"{self.parse_expression(node.value, indent)}[{self.parse_expression(node.slice, indent)}]"
