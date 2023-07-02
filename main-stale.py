import ast

rows, cols = (20, 20)
grid = [[0 for i in range(cols)] for j in range(rows)]
code = ""
code = """
x = 1
y = 2

height = 3
width = 4


for i in range(width):
    grid[x][y + i] = 1
    grid[x + height - 1][y + i] = 1

for i in range(height):
    grid[x + i][y] = 1
    grid[x + i][y + width - 1] = 1


"""
if grid:
    for row in grid:
        for e in row:
            print(e, end="")
        print()

tree = ast.parse(code)


print(ast.dump(tree, indent=4))


def print_indented(*args, indentor=" ", indent=0, **kwargs):
    print(indentor * indent, *args, **kwargs)


def codeGen(theType):
    def _subscript(node: ast.Subscript, print: callable, traverse: callable):
        print(ast.dump(node))

    def _assign(node: ast.Assign, print: callable, traverse: callable):
        pass

    def _name(node: ast.Name, print: callable, traverse: callable):
        print(node.id, end="")
        pass

    def _store(node: ast.Store, print: callable, travsere: callable):
        pass

    def _constant(node: ast.Constant, _print: callable, traverse: callable):
        print(" = ", node.value)

    def _for(node: ast.For, print: callable):
        print("for (", end="")

    def _module(node: ast.Module, print: callable, traverse: callable):
        print("called")
        for child in ast.iter_child_nodes(node):
            traverse(child)

    generate_verilog = {
        ast.Assign: _assign,
        ast.Name: _name,
        ast.Subscript: _subscript,
        ast.Store: _store,
        ast.Constant: _constant,
        ast.For: _for,
        ast.Module: _module,
    }
    try:
        return generate_verilog[theType]
    except KeyError:
        print(theType)
        return lambda x, y, z: None


def traverse(node: ast.AST, indent: int = 0):
    print = lambda *args, **kwargs: print_indented(
        *args, indent=indent, indentor=" " * 4, **kwargs
    )
    if node == None:
        return
    # print(ast.dump(node))
    _traverse = lambda node: traverse(node, indent + 1)
    codeGen(type(node))(node, print, _traverse)
    # for child in ast.iter_child_nodes(node):
    #     traverse(child, indent + 1)


traverse(tree)
