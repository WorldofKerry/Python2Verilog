from python2verilog.frontend import Generator2Graph
import unittest
import ast
import networkx as nx
from matplotlib import pyplot as plt
from python2verilog.ir import Context, create_networkx_adjacency_list


class TestGenerator2Graph(unittest.TestCase):
    def test_basics(self):
        return
        python = """
def circle_lines(s_x, s_y, height) -> tuple[int, int]:
    i = 0
    while i < s_y:
        i += s_x
    yield (i, height)
"""
        func = ast.parse(python).body[0]
        inst = Generator2Graph(Context(), func)

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

        # plt.savefig("path.png")
        # warnings.warn(f"{inst._root._then_edge._node}")

        plt.clf()
        plt.cla()
        plt.close()
