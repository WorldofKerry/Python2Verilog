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


from package import Python2Verilog as P2V

p2v = P2V.AstParser()
print(p2v.parse_statements(tree.body))
