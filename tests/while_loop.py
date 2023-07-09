from setup import python2verilog as p2v, output, input

code = ""

code = """
def draw_rectangle(s_x, s_y, height, width) -> tuple[int, int]:
    counter = 0
    while (counter < height): 
        yield(counter, counter)
        counter = counter + 1

"""
exec(code)
rows, cols = (20, 20)
generator = draw_rectangle(1, 2, 3, 4)
grid = [[0 for i in range(cols)] for j in range(rows)]

with output(__file__, "expected", "csv") as f:
    for x, y in generator:
        grid[x][y] = 1
        f.write(f"{x}, {y}\n")

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

        exp_coords = set()
        act_coords = set()

        for row in actual:
            if row[1].strip() != "x" and row[2].strip() != "x":
                exp_coords.add((row[1].strip(), row[2].strip()))

        for row in expected:
            act_coords.add((row[0].strip(), row[1].strip()))

        if exp_coords - act_coords:
            print("ERROR: missing coordinates" + str(exp_coords - act_coords))
        if act_coords - exp_coords:
            print("ERROR: extra coordinates" + str(act_coords - exp_coords))
        print("PASS")
