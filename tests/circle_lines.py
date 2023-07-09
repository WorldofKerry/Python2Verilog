from setup import python2verilog as p2v, output, input

code = ""

# Circle Algorithm
code = """
def draw_rectangle(s_x, s_y, height, width) -> tuple[int, int]:
    x = 0
    y = height
    d = 3 - 2 * height
    yield (s_x + x, s_y + y)
    yield (s_x + x, s_y - y)
    yield (s_x - x, s_y + y)
    yield (s_x - x, s_y - y)
    yield (s_x + y, s_y + x)
    yield (s_x + y, s_y - x)
    yield (s_x - y, s_y + x)
    yield (s_x - y, s_y - x)
    while (y >= x):
        x = x + 1
        if (d > 0):
            y = y - 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6
        yield (s_x + x, s_y + y)
        yield (s_x + x, s_y - y)
        yield (s_x - x, s_y + y)
        yield (s_x - x, s_y - y)
        yield (s_x + y, s_y + x)
        yield (s_x + y, s_y - x)
        yield (s_x - y, s_y + x)
        yield (s_x - y, s_y - x)
"""
exec(code)
rows, cols = (100, 100)
generator = draw_rectangle(23, 17, 5, None) # x, y, radius
grid = [[0 for i in range(cols)] for j in range(rows)]

with output(__file__, "expected", "csv") as f:
    counter = 0
    for x, y in generator:
        grid[x][y] = 1
        f.write(f"{x}, {y}\n")
        counter += 1
    print(f"Python took {counter} cycles")


with output(__file__, "visual") as f:
    if grid:
        for row in grid:
            for e in row:
                f.write(f"{e}")
            f.write("\n")

    import ast

    tree = ast.parse(code)
    f.write(ast.dump(tree, indent=4))

with output(__file__, "module", "sv") as f:
    from setup import python2verilog as p2v

    func = tree.body[0]
    genParser = p2v.GeneratorParser(func)
    f.write(str(genParser.generate_verilog()))

import csv

with input(__file__, "expected", "csv") as exp_f:
    with input(__file__, "actual", "csv") as act_f:
        expected = csv.reader(exp_f)
        actual = csv.reader(act_f)

        actual_coords = set()
        expected_coords = set()

        for row in actual:
            if row[1].strip() != "x" and row[2].strip() != "x":
                actual_coords.add((row[1].strip(), row[2].strip()))

        for row in expected:
            expected_coords.add((row[0].strip(), row[1].strip()))

        if actual_coords - expected_coords:
            print("ERROR: extra coordinates" + str(actual_coords - expected_coords))
        if expected_coords - actual_coords:
            print("ERROR: missing coordinates" + str(expected_coords - actual_coords))
        print("PASS")
