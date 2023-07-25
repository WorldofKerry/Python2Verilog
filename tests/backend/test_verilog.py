from python2verilog.backend.verilog import (
    Verilog,
    Module,
    PosedgeSyncAlways,
    Instantiation,
    Expression,
)
from python2verilog.frontend import GeneratorParser, Generator2Graph
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
        # module = Verilog.create_module_from_python(tree.body[0])
        # warnings.warn(module.to_lines()[0].to_string())


class TestVerilog(unittest.TestCase):
    def test_module(self):
        module = Module("cool_name", ["in0"], ["out0"])
        lines = module.to_lines()
        assert_lines(
            self,
            lines.to_string(),
            "module cool_name ( \n input wire [31:0] in0,\n input wire _start, \n input wire _clock, \n output reg [31:0] out0, \n output reg _done, \n output reg _valid  \n ); \n endmodule",
        )

    def test_always(self):
        always = PosedgeSyncAlways(Expression("_clock"), valid="_valid")
        lines = always.to_lines()
        # assert_lines(
        #     self,
        #     lines.to_string(),
        #     "always @(posedge _clock) begin \n _valid <= 0; \n end",
        # )

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
        ir = GeneratorParser(function)
        verilog = Verilog()
        verilog.from_ir(ir.get_root(), ir.get_context())
        # warnings.warn(verilog.get_module())
        # warnings.warn(
        #     verilog.get_testbench_improved([(17, 23, 15), (4, 5, 6), (1, 2, 3)])
        #     .to_lines()
        #     .to_string()
        # )

    def test_instantiation(self):
        ports = {"_clock": "CLK", "_valid": "_valid"}
        inst = Instantiation("module0", "my_module", ports)
        # warnings.warn(inst.to_lines())


import networkx as nx
from matplotlib import pyplot as plt
from python2verilog import ir


class TestNewGraphIR(unittest.TestCase):
    def test_basics(self):
        python = """
def fib(n: int) -> tuple[int]:
    a = 0
    b = 1
    c = 0
    count = 1
    while count < n:
        count += 1
        a = b
        b = c
        c = a + b
        yield (c,)
"""
        func = ast.parse(python).body[0]
        inst = Generator2Graph(func)

        adjacency_list = ir.create_adjacency_list(inst._root)
        g = nx.DiGraph(adjacency_list)

        plt.figure(figsize=(20, 20))
        nx.draw(
            g,
            with_labels=True,
            font_weight="bold",
            arrowsize=30,
            node_size=4000,
            node_shape="s",
            node_color="#00b4d9",
        )
        # plt.savefig("path.png")

        verilog = Verilog()
        verilog.from_ir_graph(inst._root, inst.get_context())
        warnings.warn(verilog.get_module())
        # warnings.warn(verilog.get_testbench([(10,)]).to_lines().to_string())
