import ast
import dis
import logging
import unittest

import networkx as nx
from matplotlib import pyplot as plt

from python2verilog import (
    Modes,
    get_actual_raw,
    get_context,
    get_expected,
    namespace_to_file,
    namespace_to_verilog,
    verilogify,
)
from python2verilog import ir
from python2verilog.frontend import FromGenerator
from python2verilog.ir import Context, create_networkx_adjacency_list


class TestGenerator2Graph(unittest.TestCase):
    def test_multi_assign(self):
        ns = {}

        @verilogify(namespace=ns)
        def multi_assign():
            a = 1
            b, c = 2, 3
            yield a, b, c
            # d, e, (x, y), g = 10, 20, (a, b), c

        multi_assign()

        logging.error(dis.Bytecode("d, e, (x, y), g = 10, 20, (a, b), c").dis())

        module, testbench = namespace_to_verilog(ns)

    def test_assign_visitor(self):
        code = "d, e, (x, y), g = 10, c, (a, b), 20"

        assign = ast.parse(code).body[0]

        target: ast.Tuple = assign.targets[0]
        value: ast.Tuple = assign.value

        result = FromGenerator(ir.Context.empty())._target_value_visitor(target, value)

        self.assertEqual(
            str(list(result)), "[(_d, 10), (_e, _c), (_x, _a), (_y, _b), (_g, 20)]"
        )

        code = "d, e, bruv, g = 10, 20, (a, b), c"

        # logging.error(dis.Bytecode("d, e, (x, y), g = 10, 20, (a, b), c").dis())
        assign: ast.Assign = ast.parse(code).body[0]
        # logging.error(ast.dump(tree, indent=1))

        target: ast.Tuple = assign.targets[0]
        value: ast.Tuple = assign.value

        with self.assertRaises(TypeError):
            result = FromGenerator(ir.Context.empty())._target_value_visitor(
                target, value
            )
            list(result)
