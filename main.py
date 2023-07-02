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
    assert len(node.args) == 2
    return (
        str(node.args[0].value)
        + "; "
        + iteratorName
        + " < "
        + node.args[1].id
        + "; i++) {"
        + "\n"
    )


def parse_for(node: ast.For, indent: int = 0) -> str:
    buffer = (
        "For(int " + node.target.id + " " + stringify_range(node.iter, node.target.id)
    )
    buffer += parse_body(node.body, indent + 1)
    return buffer


def parse_targets(nodes: list[ast.AST], indent: int = 0) -> str:
    buffer = ""
    for node in nodes:
        if isinstance(node, ast.Subscript):
            buffer += parse_subscript(node, indent)
        else:
            print("Error: unexpected target")
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
    return buffer


def parse_slice(node: ast.AST, indent: int = 0) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.BinOp):
        return parse_slice(node.left) + " + " + parse_slice(node.right)
    if isinstance(node, ast.Constant):
        return str(node.value)
    print("Error: unexpected slice", type(node))
    return ""


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
    return ""


def parse_subscript(node: ast.Subscript, indent: int = 0) -> str:
    if not node:
        return ""
    buffer = parse_value(node.value, indent)
    buffer += parse_slice(node.slice, indent)
    return buffer


print(parse_for(forLoop))
