import ast
import logging
import textwrap
import unittest
import inspect
from python2verilog.ir import expressions as expr
from python2verilog.ir.ssa import SSA


class TestSSA(unittest.TestCase):
    def test_main(self):
        def basic_func(d):
            a = 42
            b = a
            c = a + b

            a = c + 23
            # c = a + d

        source = textwrap.dedent(inspect.getsource(basic_func))
        tree = ast.parse(source)
        func = tree.body[0]

        # logging.error(ast.dump(func, indent=1))

        ssa = SSA()
        result = ssa.parse_stmts("block1", func.body)
        logging.error(result)
