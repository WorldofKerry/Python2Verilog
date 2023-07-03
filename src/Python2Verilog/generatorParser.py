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

    def setup_func_return(self, node: ast.AST, prefix: str) -> str:
        """
        Parser for FunctionDef.returns
        """
        assert type(node) == ast.Subscript
        assert type(node.slice) == ast.Tuple
        return [f"{prefix}_out{str(i)}" for i in range(len(node.slice.elts))]

    def get_unique_name(self) -> str:
        self.unique_name_counter += 1
        return f"{self.unique_name_counter}"

    def add_unique_global_var(self, initial_value: str, name_prefix: str = "") -> None:
        name = f"{name_prefix}_{self.get_unique_name()}"
        self.add_global_var(initial_value, name)
        return name

    def add_global_var(self, initial_value: str, name: str) -> None:
        self.global_vars[name] = initial_value
        return name

    def stringify_var_declaration(self) -> str: 
        """
        Requires self.global_vars to be complete
        """
        buffer = ""

    def generate_verilog(self, indent: int = 0) -> str:
        moduleStart, moduleEnd = self.create_module_header_footer(indent)
        self.buffer = indentify(indent, moduleStart)  # module name(...)

        (
            initializationStartBuffer,
            initializationEndBuffer,
        ) = self.generate_initialization()
        body = buffer_indentify(indent + 1, initializationStartBuffer)  # if (_start)

        body += indentify(indent + 2, "always @(posedge _clock) begin\n")
        body += self.parse_statements(
            self.root.body, indent=indent + 3, prefix=f"_{self.name}"
        )

        # TODO: not have functions mutate self.global_vars
        for var in self.global_vars:
            self.buffer += indentify(indent + 1, f"reg [31:0] {var};\n")
        self.buffer += "\n"

        self.buffer += body

        self.buffer += indentify(indent + 2, "end\n\n")

        self.buffer += buffer_indentify(indent + 1, initializationEndBuffer)

        self.buffer += indentify(indent, moduleEnd)

        return self.buffer

    def generate_initialization(self) -> tuple[list[str], list[str]]:
        startBuffers = []
        endBuffers = []
        startBuffers.append(f"if (_start) begin\n")
        startBuffers.append(indentify(1, "_done = 0;\n"))
        for v in self.global_vars:
            startBuffers.append(indentify(1, f"{v} = {self.global_vars[v]};\n"))
        startBuffers.append(f"end else begin\n")
        endBuffers.append("end\n")
        return [startBuffers, endBuffers]

    def create_module_header_footer(self, indent: int) -> tuple[str, str]:
        startBuffer = f"module {self.name}(\n"
        startBuffer += indentify(indent + 1, "input wire _clock,\n")
        startBuffer += indentify(indent + 1, "input wire _start,\n")
        for var in self.root.args.args:
            startBuffer += indentify(indent + 1, f"input wire [31:0] {var.arg},\n")
        for var in self.yieldVars:
            startBuffer += indentify(indent + 1, f"output wire [31:0] {var},\n")
        startBuffer += indentify(indent + 1, "output reg _done,\n")
        startBuffer = startBuffer.removesuffix(",\n") + "\n);\n"
        endBuffer = "endmodule"
        return [startBuffer, endBuffer]

    def __init__(self, root: ast.FunctionDef):
        self.name = root.name
        self.yieldVars = self.setup_func_return(root.returns, f"_{root.name}")
        self.unique_name_counter = 0
        self.global_vars: dict[str, str] = {}
        self.root = root

    def stringify_range(self, node: ast.Call, iteratorName: str) -> str:
        assert node.func.id == "range"
        if len(node.args) == 2:
            start, end = str(node.args[0].value), node.args[1].id
        else:
            start, end = "0", node.args[0].id
        return start + "; " + iteratorName + " < " + end + "; i++) {" + "\n"

    def parse_for(self, node: ast.For, indent: int = 0, prefix: str = "") -> str:
        def parse_iter(node: ast.AST) -> tuple[str, str, str]:
            assert type(node) == ast.Call
            assert node.func.id == "range"
            if len(node.args) == 2:
                start, end = str(node.args[0].value), node.args[1].id
            else:
                start, end = "0", node.args[0].id
            name = self.add_unique_global_var(start, f"{prefix}_FOR_ITER")
            return [
                f"if ({name} < {end}) {prefix}_STATE++; // FOR LOOP START\n",
                "else begin\n",
                "end // FOR LOOP END\n",
            ]

        iterStart0, iterStart1, iterEnd = parse_iter(node.iter)
        buffer = indentify(indent, iterStart0)
        buffer += indentify(indent, iterStart1)
        buffer += self.parse_statements(node.body, indent + 1, f"{prefix}_INNER")
        buffer += indentify(indent, iterEnd)
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

    def parse_statements(self, stmts: list[ast.AST], indent: int, prefix: str) -> str:
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
