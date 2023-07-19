import unittest
import ast
import warnings

from python2verilog.optimizer import replace_single_case
from python2verilog.frontend import GeneratorParser
from python2verilog.backend import Verilog


class TestOptimizer(unittest.TestCase):
    def test_replace_single_case(self):
        python = """
def foo(x) -> tuple[int]:
    if x > 0:
        yield 1
    else:
        yield 1
"""
        tree = ast.parse(python)
        function = tree.body[0]
        ir, context = GeneratorParser(function).get_results()
        ir = replace_single_case(ir)
        verilog = Verilog().from_ir(ir, context)
        warnings.warn(verilog.get_module().to_string())
