import ast

rows, cols = (20, 20)
grid = [[0 for i in range(cols)] for j in range(rows)]
code = ""
code = """
x = 1
y = 2

height = 3
width = 4


for i in range(0, width):
    grid[x][y + i] = 1
    grid[x + height - 1][y + i] = 1

for i in range(height):
    grid[x + i][y] = 1
    grid[x + i][y + width - 1] = 1


"""
# if grid:
#     for row in grid:
#         for e in row:
#             print(e, end="")
#         print()

tree = ast.parse(code)


# print(ast.dump(tree, indent=4))


def dump(node: ast.AST):
    return ast.dump(node)


forLoop = tree.body[4]
# print(dump(forLoop))


def indentify(indent: int, text: str, *args, **kwargs):
    return " " * 4 * indent + text


def stringify_range(node: ast.Call, iteratorName: str):
    # TODO: support more range function types
    assert node.func.id == "range"
    if len(node.args) == 2:
        start, end = str(node.args[0].value), node.args[1].id
    else:
        start, end = "0", node.args[0].id
    return start + "; " + iteratorName + " < " + end + "; i++) {" + "\n"


def parse_for(node: ast.For, indent: int = 0) -> str:
    buffer = indentify(
        indent,
        "For(int "
        + node.target.id
        + " = "
        + stringify_range(node.iter, node.target.id),
    )

    buffer += parse_body(node.body, indent + 1)
    buffer += indentify(indent, "}\n")
    return buffer


def parse_targets(nodes: list[ast.AST], indent: int = 0) -> str:
    buffer = ""
    assert len(nodes) == 1
    for node in nodes:
        buffer += parse_value(node, indent)
    return buffer


def parse_assign(node: ast.Assign, indent: int = 0) -> str:
    buffer = indentify(indent, "")
    buffer += parse_targets(node.targets, indent)
    buffer += " = "
    buffer += parse_value(node.value, indent)
    buffer += "\n"
    return buffer


def parse_body(nodes: list[ast.AST], indent: int = 0) -> str:
    buffer = ""
    for node in nodes:
        # buffer += indentify(indent, dump(child)) + "\n"
        if isinstance(node, ast.Assign):
            buffer += parse_assign(node, indent)
        elif isinstance(node, ast.For):
            buffer += parse_for(node, indent)
        else:
            print("Error: unexpected body")
    return buffer


def parse_value(node: ast.AST, indent: int = 0) -> str:
    if isinstance(node, ast.Constant):
        # print("a")
        return str(node.value)
    if isinstance(node, ast.Name):
        # print("b", node.id)
        return node.id
    if isinstance(node, ast.Subscript):
        # print("c")
        return parse_subscript(node, indent)
    if isinstance(node, ast.BinOp):
        return parse_value(node.left) + " + " + parse_value(node.right)
    return ""


def parse_subscript(node: ast.Subscript, indent: int = 0) -> str:
    if not node:
        return ""
    buffer = parse_value(node.value, indent)
    buffer += "[" + parse_value(node.slice, indent) + "]"
    return buffer


# print(parse_for(forLoop))
print(parse_body(tree.body))
