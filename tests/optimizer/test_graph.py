import logging
import unittest

import networkx as nx
from matplotlib import pyplot as plt

from python2verilog.ir.expressions import *  # nopycln: import
from python2verilog.ir.graph2 import *  # nopycln: import


class TestGraph(unittest.TestCase):
    def test_graph2(self):
        out = Var("out")
        i = Var("i")
        n = Var("n")
        a = Var("a")
        b = Var("b")

        graph = Graph()

        root = graph.add_node(AssignNode(i, Int(0)))
        prev = root

        prev = graph.add_node(ClockNode(), prev)
        if_i_lt_n = graph.add_node(BranchNode(BinOp(i, "<", n)), prev)

        prev = graph.add_node(TrueNode(), if_i_lt_n)
        if_a_mod_2 = graph.add_node(BranchNode(Mod(a, Int(2))), prev)
        prev = graph.add_node(TrueNode(), if_a_mod_2)
        prev = graph.add_node(AssignNode(out, a), prev)
        prev = graph.add_node(ClockNode(), prev)
        graph.add_node(FalseNode(), if_a_mod_2, children=[prev])
        a_assign_b = graph.add_node(AssignNode(a, b), prev)
        b_assign_a_plus_b = graph.add_node(AssignNode(b, BinOp(a, "+", b)), prev)
        prev = graph.add_node(ClockNode(), a_assign_b, b_assign_a_plus_b)
        prev = graph.add_node(
            AssignNode(i, BinOp(i, "+", Int(1))), prev, children=[if_i_lt_n]
        )

        logging.error(prev)
        logging.error(graph)

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape()))
