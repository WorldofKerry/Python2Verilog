from python2verilog.backend.codegen import Verilog, Module
from python2verilog.frontend import Generator2Ast
import unittest
import warnings
import ast


def assert_lines(test_case: unittest.TestCase, first: str, second: str):
    """
    Asserts that each stripped line in first matches each stripped line in second
    """
    test_case.assertTrue(isinstance(first, str) and isinstance(second, str))
    for a_line, b_line in zip(first.splitlines(), second.splitlines()):
        test_case.assertEqual(a_line.strip(), b_line.strip())


class TestVerilog(unittest.TestCase):
    def test_module(self):
        module = Module("cool_name", ["_start", "_clock", "in0"], ["_done", "out0"])
        lines = module.to_lines()
        assert_lines(
            self,
            lines[0].to_string(),
            "module cool_name( \n input wire _start, \n input wire _clock,\n input wire in0,\n output reg _done, \noutput reg out0 \n );",
        )
        assert_lines(self, lines[1].to_string(), "endmodule")

    def test_constructor(self):
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
