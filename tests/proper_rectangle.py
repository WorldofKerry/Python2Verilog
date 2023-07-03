code = """
def draw_rectangle(s_x, s_y, height, width) -> tuple[int, int]:
    for i0 in range(0, width):
        yield (s_x, s_y + i0)
        yield (s_x + height - 1, s_y + i0)

    for i1 in range(height):
        yield (s_x + i1, s_y)
        yield (s_x + i1, s_y + width - 1)

"""
exec(code)
rows, cols = (20, 20)
generator = draw_rectangle(1, 2, 3, 4)
grid = [[0 for i in range(cols)] for j in range(rows)]

for x, y in generator:
    grid[x][y] = 1
    print(x, y)
if grid:
    for row in grid:
        for e in row:
            print(e, end="")
        print()

import ast

tree = ast.parse(code)
print(ast.dump(tree, indent=4))

from package import python2verilog as p2v

func = tree.body[0]
genParser = p2v.GeneratorParser(func)
print(genParser.generate_verilog())
