from python2verilog.backend.codegen import (
    Verilog,
    Module,
    Always,
    create_module_from_python,
)
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


class TestHelpers(unittest.TestCase):
    def test_verilog_helpers(self):
        code = "def func(a, b, c, d) -> tuple[int, int]:\n  yield(a, b)\n  yield(c, d)"
        tree = ast.parse(code)
        module = create_module_from_python(tree.body[0])
        # warnings.warn(module.to_lines()[0].to_string())


class TestVerilog(unittest.TestCase):
    def test_module(self):
        module = Module("cool_name", ["in0"], ["out0"])
        lines = module.to_lines()
        assert_lines(
            self,
            lines[0].to_string(),
            "module cool_name( \n input wire [31:0] in0,\n input wire _start, \n input wire _clock, \n output reg [31:0] out0, \n output reg _done, \n output reg _valid  \n );",
        )
        assert_lines(self, lines[1].to_string(), "endmodule")

    def test_always(self):
        always = Always("_clock", "_valid")
        lines = always.to_lines()
        assert_lines(
            self,
            lines[0].to_string(),
            "always @(posedge _clock) begin \n _valid <= 0; \n",
        )
        assert_lines(self, lines[1].to_string(), "end")

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
        function = tree.body[0]
        ir_generator = Generator2Ast(function)
        output = ir_generator.parse_statements(function.body, "")
        # warnings.warn(output.to_lines())
        verilog = Verilog()
        verilog.from_ir(output, ir_generator.global_vars)
        verilog.setup_from_python(function)
        # warnings.warn(verilog.get_module())
        # warnings.warn(verilog.get_testbench((17, 23, 15)))
