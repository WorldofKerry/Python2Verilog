import ast


def indentify(indent: int = 0, text: str = "") -> str:
    return " " * 4 * indent + text


def buffer_indentify(indent: int = 0, buffers: list[str] = []) -> str:
    output = ""
    for buffer in buffers:
        output += indentify(indent, buffer)
    return output


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

    def stringify_var_declaration(self, indent: int) -> list[str]:
        """
        reg [31:0] <name>
        Warning: requires self.global_vars to be complete
        """
        buffers = []
        for var in self.global_vars:
            buffers.append(f"reg [31:0] {var}\n")
        return buffers

    def stringify_always_block(self):
        """
        always @(posedge _clock) begin
        end
        """
        return [["always @(posedge _clock) begin\n"], ["end\n"]]

    def generate_verilog(self, indent: int = 0) -> str:
        """
        Master function
        """
        body_string = self.parse_statements(
            self.root.body, indent + 3, f"_{self.name}", outermostStatements=True
        )  # TODO: remove 'arbitrary' + 3
        moduleStartBuffers, moduleEndBuffers = self.stringify_module()
        alwaysStartBuffers, alwaysEndBuffers = self.stringify_always_block()
        initStartBuffers, initEndBuffers = self.stringify_init()

        self.buffer = ""
        self.buffer += buffer_indentify(indent, moduleStartBuffers)
        self.buffer += buffer_indentify(indent + 1, alwaysStartBuffers)
        self.buffer += buffer_indentify(indent + 2, initStartBuffers)
        self.buffer += body_string
        self.buffer += buffer_indentify(indent + 2, initEndBuffers)
        self.buffer += buffer_indentify(indent + 1, alwaysEndBuffers)
        self.buffer += buffer_indentify(indent, moduleEndBuffers)

        return self.buffer

    def stringify_init(self) -> tuple[list[str], list[str]]:
        """
        if (_start) begin
            <var> = <value>;
            ...
        end else begin
        ...
        end
        """
        startBuffers = []
        endBuffers = []
        startBuffers.append(f"if (_start) begin\n")
        startBuffers.append(indentify(1, "_done = 0;\n"))
        for v in self.global_vars:
            startBuffers.append(indentify(1, f"{v} = {self.global_vars[v]};\n"))
        startBuffers.append(f"end else begin\n")
        endBuffers.append("end\n")
        return [startBuffers, endBuffers]

    def stringify_module(self) -> tuple[list[str], list[str]]:
        """
        module <name>(...);
        endmodule
        """
        startBuffers, endBuffers = [], []
        startBuffers.append(f"module {self.name}(\n")
        startBuffers.append(indentify(1, "input wire _clock;\n"))
        startBuffers.append(indentify(1, "input wire _start;\n"))
        for var in self.root.args.args:
            startBuffers.append(indentify(1, f"input wire [31:0] {var.arg},\n"))
        for var in self.yieldVars:
            startBuffers.append(indentify(1, f"output wire [31:0] {var},\n"))
        startBuffers.append(indentify(1, "output reg _done,\n"))
        startBuffers[-1] = startBuffers[-1].removesuffix(",\n") + "\n);\n"
        endBuffers.append("endmodule")
        return [startBuffers, endBuffers]

    def __init__(self, root: ast.FunctionDef):
        self.name = root.name
        self.yieldVars = self.generate_return_vars(root.returns, f"_{root.name}")
        self.unique_name_counter = 0
        self.global_vars: dict[str, str] = {}
        self.root = root

    def parse_for(self, node: ast.For, indent: int = 0, prefix: str = "") -> str:
        def parse_iter(node: ast.AST) -> tuple[list[str], list[str]]:
            assert type(node) == ast.Call
            assert node.func.id == "range"
            if len(node.args) == 2:
                start, end = str(node.args[0].value), node.args[1].id
            else:
                start, end = "0", node.args[0].id
            name = self.add_unique_global_var(start, f"{prefix}_FOR_ITER")
            return [[
                f"if ({name} < {end}) {prefix}_STATE++; // FOR LOOP START\n",
                "else begin\n"],[
                "end // FOR LOOP END\n"],
            ]

        startBuffers, endBuffers = parse_iter(node.iter)
        buffer = buffer_indentify(indent, startBuffers)
        buffer += self.parse_statements(node.body, indent + 1, f"{prefix}_INNER")
        buffer += buffer_indentify(indent, endBuffers)
        return buffer

    def parse_targets(self, nodes: list[ast.AST], indent: int = 0) -> str:
        buffer = ""
        assert len(nodes) == 1
        for node in nodes:
            buffer += self.parse_expression(node, indent)
        return buffer

    def parse_assign(self, node: ast.Assign, indent: int = 0) -> str:
        buffer = indentify(indent)
        buffer += self.parse_targets(node.targets, indent)
        buffer += " = "
        buffer += self.parse_expression(node.value, indent)
        buffer += "\n"
        return buffer

    def parse_statement(self, stmt: ast.AST, indent: int, prefix: str = "") -> str:
        match type(stmt):
            case ast.Assign:
                return self.parse_assign(stmt, indent)
            case ast.For:
                return self.parse_for(stmt, indent, prefix)
            case ast.Expr:
                return self.parse_statement(stmt.value, indent)
            case ast.Yield:
                return self.parse_yield(stmt, indent, prefix)
            case _:
                print("Error: unexpected statement type", type(stmt))
                return ""

    def parse_statements(
        self,
        stmts: list[ast.AST],
        indent: int,
        prefix: str,
        outermostStatements: bool = False,
    ) -> str:
        state_var = self.add_global_var("0", f"{prefix}_STATE")
        buffer = indentify(indent, f"case ({state_var})\n")
        state_counter = 0
        for stmt in stmts:
            state = self.add_global_var(
                str(state_counter), f"{prefix}_STATE_{state_counter}"
            )
            state_counter += 1

            buffer += indentify(indent + 1, f"{state}: begin\n")
            buffer += self.parse_statement(stmt, indent + 2, prefix)
            if type(stmt) != ast.For:
                # TODO: better conditionals
                buffer += indentify(indent + 2, f"{state_var} <= {state_var} + 1;\n")
            buffer += indentify(indent + 1, f"end\n")

        if outermostStatements:
            buffer = buffer.removesuffix(indentify(indent + 1, f"end\n"))
            buffer += indentify(indent + 2, f"_done = 1;\n")
            buffer += indentify(indent + 1, f"end\n")

        buffer += indentify(indent, f"endcase\n")
        return buffer

    def parse_yield(self, node: ast.Yield, indent: int, prefix: str) -> str:
        assert type(node.value) == ast.Tuple
        buffer = ""
        for i, e in enumerate(node.value.elts):
            buffer += indentify(
                indent,
                self.yieldVars[i] + " = " + self.parse_expression(e, indent) + "\n",
            )
        return buffer

    def parse_expression(self, expr: ast.AST, indent: int = 0) -> str:
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
                    + " + "
                    + self.parse_expression(expr.right)
                )
            case _:
                print("Error: unexpected expression type", type(expr))
                return ""

    def parse_subscript(self, node: ast.Subscript, indent: int = 0) -> str:
        return f"{self.parse_expression(node.value, indent)}[{self.parse_expression(node.slice, indent)}]"
