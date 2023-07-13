from python2verilog.frontend import Generator2Ast
import unittest
import ast
import warnings


class TestGenerator2Ast(unittest.TestCase):
    def test_all(self):
        func = """
def circle_lines(s_x, s_y, height) -> tuple[int, int]:
    a = 123
    yield(a, height)
    s_y = a
    yield(s_x, s_y)
        """
        generatorParser = Generator2Ast(ast.parse(func).body[0])
        warnings.warn((generatorParser.generate_verilog()))
