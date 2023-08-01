from python2verilog.frontend import Generator2List, Generator2Graph
import unittest
import ast
import warnings


class TestGeneratorParser(unittest.TestCase):
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
        generatorParser = Generator2List(tree.body[0])

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
        generatorParser = Generator2List(tree.body[0])

        with open("module_circle.log", mode="w") as module_file:
            module_file.write(generatorParser.generate_verilog().to_string())


import networkx as nx
from matplotlib import pyplot as plt
from python2verilog.ir import *


class TestGenerator2Graph(unittest.TestCase):
    def test_basics(self):
        python = """
def circle_lines(s_x, s_y, height) -> tuple[int, int]:
    i = 0
    while i < s_y:
        i += s_x
    yield (i, height)
"""
        func = ast.parse(python).body[0]
        inst = Generator2Graph(func)

        adjacency_list = create_networkx_adjacency_list(inst._root)
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

        plt.savefig("path.png")
        # warnings.warn(f"{inst._root._then_edge._node}")

        plt.clf()
        plt.cla()
        plt.close()
