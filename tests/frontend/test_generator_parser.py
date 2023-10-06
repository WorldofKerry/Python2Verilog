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

        multi_assign()

        module, testbench = namespace_to_verilog(ns)
