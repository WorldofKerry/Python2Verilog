from python2verilog.backend.codegen import Verilog
from python2verilog.frontend import Generator2Ast
import unittest
import warnings
import ast


class TestVerilog(unittest.TestCase):
    def test_all(self):
        code = """
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
        # yield (x, y, d)
        yield (s_x + x, s_y + y)
        yield (s_x + x, s_y - y)
        yield (s_x - x, s_y + y)
        yield (s_x - x, s_y - y)
        yield (s_x + y, s_y + x)
        yield (s_x + y, s_y - x)
        yield (s_x - y, s_y + x)
        yield (s_x - y, s_y - x)
"""
        tree = ast.parse(code)
        # warnings.warn(ast.dump(tree.body[0]))
        generator_inst = Generator2Ast(tree.body[0])
        output = generator_inst.parse_statements(tree.body[0].body, "")
        # warnings.warn(output.to_lines())
        ver = Verilog(output)
        ver_result = ver.build_tree(output)
        # warnings.warn(ver_result.to_string())
