import ast


__all__ = ["AstParser"]


class AstParser:
    def indentify(self, indent: int, text: str) -> str:
        return " " * 4 * indent + text

    def stringify_range(self, node: ast.Call, iteratorName: str) -> str:
        # TODO: support more range function types
        assert node.func.id == "range"
        if len(node.args) == 2:
            start, end = str(node.args[0].value), node.args[1].id
        else:
            start, end = "0", node.args[0].id
        return start + "; " + iteratorName + " < " + end + "; i++) {" + "\n"

    def parse_for(self, node: ast.For, indent: int = 0) -> str:
        buffer = self.indentify(
            indent,
            "For(int "
            + node.target.id
            + " = "
            + self.stringify_range(node.iter, node.target.id),
        )

        buffer += self.parse_statements(node.body, indent + 1)
        buffer += self.indentify(indent, "}\n")
        return buffer

    def parse_targets(self, nodes: list[ast.AST], indent: int = 0) -> str:
        buffer = ""
        assert len(nodes) == 1
        for node in nodes:
            buffer += self.parse_expression(node, indent)
        return buffer

    def parse_assign(self, node: ast.Assign, indent: int = 0) -> str:
        buffer = self.indentify(indent, "")
        buffer += self.parse_targets(node.targets, indent)
        buffer += " = "
        buffer += self.parse_expression(node.value, indent)
        buffer += "\n"
        return buffer

    def parse_statement(self, node: ast.AST, indent: int = 0) -> str:
        match type(node):
            case ast.Assign:
                return self.parse_assign(node, indent)
            case ast.For:
                return self.parse_for(node, indent)
            case _:
                print("Error: unexpected statement type")
                return ""

    def parse_statements(self, statement: list[ast.AST], indent: int = 0) -> str:
        buffer = ""
        for node in statement:
            buffer += self.parse_statement(node, indent)
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
                print("Error: unexpected expression type")
                return ""

    def parse_subscript(self, node: ast.Subscript, indent: int = 0) -> str:
        return f"{self.parse_expression(node.value, indent)}[{self.parse_expression(node.slice, indent)}]"
