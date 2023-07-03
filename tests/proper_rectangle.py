code = ""

code = """
def draw_rectangle(s_x, s_y, height, width) -> tuple[int, int]:
    for i in range(0, width):
        yield (s_x, s_y + i)
        yield (s_x + height - 1, s_y + i)

    for i in range(height):
        yield (s_x + i, s_y)
        yield (s_x + i, s_y + width - 1)

"""
exec(code)
rows, cols = (20, 20)
generator = draw_rectangle(1, 2, 10, 15)
grid = [[0 for i in range(cols)] for j in range(rows)]
try:
    while True:
        x, y = next(generator)
        grid[x][y] = 1
except StopIteration:
    pass
if grid:
    for row in grid:
        for e in row:
            print(e, end="")
        print()

import ast


tree = ast.parse(code)
print(ast.dump(tree, indent=4))

from package import Python2Verilog as P2V

p2v = P2V.GeneratorParser(tree.body[0])
print(p2v.parse_statements(tree.body[0].body))
