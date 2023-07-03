import ast


def indentify(indent: int = 0, text: str = "") -> str:
    return " " * 4 * indent + text


class GeneratorParser:
    """
    Parses python generator functions
    """

    def parse_return(self, node: ast.AST, functionName: str) -> str:
        """
        Parser for FunctionDef.returns
        """
        assert type(node) == ast.Subscript
        assert type(node.slice) == ast.Tuple
        return [f"_OUTPUT_{functionName}_{str(i)}" for i in range(len(node.slice.elts))]

    def getUniqueName(self) -> str:
        self.unique_name_counter += 1
        return f"{self.unique_name_counter}"

    def add_unique_global_var(self, initial_value: str, name_prefix: str = "") -> None:
        name = f"{name_prefix}_{self.getUniqueName()}"
        self.add_global_var(initial_value, name)
        return name

    def add_global_var(self, initial_value: str, name: str) -> None:
        self.global_vars[name] = initial_value

    def getVerilog(self) -> str:
        return self.buffer

    def __init__(self, root: ast.FunctionDef):
        self.name = root.name
        self.yieldVars = self.parse_return(root.returns, root.name)
        self.unique_name_counter = 0
        self.global_vars: dict[str, str] = {}

        self.buffer = ""
        body = f"case (_{self.name}_STATE)\n"
        body += self.parse_statements(root.body, indent=1, prefix=f"_{self.name}")
        self.add_global_var("0", f"_{self.name}_STATE")
        for var in self.global_vars:
            self.buffer += f"int {var} = {self.global_vars[var]};\n"
        self.buffer += body

    def stringify_range(self, node: ast.Call, iteratorName: str) -> str:
        assert node.func.id == "range"
        if len(node.args) == 2:
            start, end = str(node.args[0].value), node.args[1].id
        else:
            start, end = "0", node.args[0].id
        return start + "; " + iteratorName + " < " + end + "; i++) {" + "\n"

    def parse_for(self, node: ast.For, indent: int = 0, prefix: str = "") -> str:
        def parse_iter(node: ast.AST) -> str:
            assert type(node) == ast.Call
            assert node.func.id == "range"
            if len(node.args) == 2:
                start, end = str(node.args[0].value), node.args[1].id
            else:
                start, end = "0", node.args[0].id
            name = self.add_unique_global_var(start, "_FOR_ITER")
            return f"if ({name} < {end}) {prefix}_STATE++;\n"

        state = f"{prefix}_STATE_{self.getUniqueName()}"
        buffer = indentify(indent, f"{state}: begin\n")
        buffer += indentify(indent + 1, parse_iter(node.iter))
        buffer += self.parse_statements(node.body, indent + 1)
        buffer += indentify(indent, "end\n")
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

    def parse_yield(self, node: ast.Yield, indent: int = 0) -> str:
        assert type(node.value) == ast.Tuple
        buffer = indentify(indent)
        for i, e in enumerate(node.value.elts):
            buffer += self.yieldVars[i] + " = " + self.parse_expression(e, indent)
            buffer += "\n"
            if i < len(node.value.elts) - 1:
                buffer += indentify(indent)
        return buffer

    def parse_statement(self, stmt: ast.AST, indent: int = 0, prefix: str = "") -> str:
        match type(stmt):
            case ast.Assign:
                return self.parse_assign(stmt, indent)
            case ast.For:
                return self.parse_for(stmt, indent, prefix)
            case ast.Expr:
                return self.parse_statement(stmt.value, indent)
            case ast.Yield:
                return self.parse_yield(stmt, indent)
            case _:
                print("Error: unexpected statement type", type(stmt))
                return ""

    def parse_statements(
        self, stmts: list[ast.AST], indent: int = 0, prefix: str = ""
    ) -> str:
        buffer = ""
        for stmt in stmts:
            buffer += self.parse_statement(stmt, indent, prefix)
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
