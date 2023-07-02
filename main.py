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
    )


def parse_for(node: ast.For, indent: int = 0):
    buffer = (
        "For(int " + node.target.id + " " + stringify_range(node.iter, node.target.id)
    )
    for child in node.body:
        buffer += indentify(indent, dump(child)) + "\n"
    return buffer


print(parse_for(forLoop))
