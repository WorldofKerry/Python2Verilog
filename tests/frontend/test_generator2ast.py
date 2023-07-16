from python2verilog.frontend import Generator2Ast
import unittest
import ast
import warnings


class TestGenerator2Ast(unittest.TestCase):
    def test_all(self):
        func = """
def circle_lines(s_x, s_y, height) -> tuple[int, int]:
    # if a < 150:
    #     a = a + 1
    # else:
    #     a = a + 2
    while a < 10:
        a = a + 1
        """
        tree = ast.parse(func)
        with open("ast.log", mode="w") as ast_file:
            ast_file.write(ast.dump(tree, indent="  "))
        generatorParser = Generator2Ast(tree.body[0])

        with open("module.log", mode="w") as module_file:
            module_file.write(generatorParser.generate_verilog().to_string())

    def test_circle_lines(self):
        func = """
def circle_lines(s_x, s_y, height) -> tuple[int, int]:
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
    while y >= x:
        x = x + 1
        if d > 0:
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
        tree = ast.parse(func)
        with open("ast_circle.log", mode="w") as ast_file:
            ast_file.write(ast.dump(tree, indent="  "))
        generatorParser = Generator2Ast(tree.body[0])

        with open("module_circle.log", mode="w") as module_file:
            module_file.write(generatorParser.generate_verilog().to_string())
