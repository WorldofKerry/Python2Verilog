import copy
import logging
import unittest

import networkx as nx
from matplotlib import pyplot as plt

from python2verilog.ir.expressions import *  # nopycln: import
from python2verilog.ir.graph2 import *
from python2verilog.optimizer.graph2optimizer import (  # nopycln: import
    dfs,
    dominance,
    dominance_frontier,
    parallelize,
    visit_nonclocked,
)


def make_even_fib_graph():
    """
    Even fib numbers
    """

    out = Var("out")
    i = Var("i")
    n = Var("n")
    a = Var("a")
    b = Var("b")

    graph = CFG()

    root = graph.add_node(ClockNode())
    graph.entry = root

    prev = graph.add_node(AssignNode(i, Int(0)), root)

    if_i_lt_n_prev = graph.add_node(ClockNode(), prev)
    prev = graph.add_node(BranchNode(BinOp(i, "<", n)), if_i_lt_n_prev)

    prev = graph.add_node(TrueNode(), prev)
    if_a_mod_2 = graph.add_node(BranchNode(Mod(a, Int(2))), prev)
    prev = graph.add_node(TrueNode(), if_a_mod_2)
    prev = graph.add_node(AssignNode(out, a), prev)
    prev = graph.add_node(ClockNode(), prev)
    graph.add_node(FalseNode(), if_a_mod_2, children=[prev])
    a_assign_b = graph.add_node(AssignNode(a, b), prev)
    b_assign_a_plus_b = graph.add_node(AssignNode(b, BinOp(a, "+", b)), prev)
    prev = graph.add_node(ClockNode(), a_assign_b, b_assign_a_plus_b)
    prev = graph.add_node(
        AssignNode(i, BinOp(i, "+", Int(1))), prev, children=[if_i_lt_n_prev]
    )
    return graph


def make_basic_graph():
    graph = CFG()
    prev = graph.add_node(ClockNode("A"))
    graph.entry = prev

    prev = graph.add_node(ClockNode("B"), prev)
    prev = graph.add_node(ClockNode("C"), prev)

    graph.add_edge(graph["B"], graph["A"])

    return graph


class TestGraph(unittest.TestCase):
    def test_graph2(self):
        graph = make_even_fib_graph()
        logging.error(graph)

        nonclocked = list(visit_nonclocked(graph, graph["7"]))
        logging.error(nonclocked)

        nonclocked = list(visit_nonclocked(graph, graph["11"]))
        logging.error(nonclocked)

        result = dominance(graph, graph.entry)[graph["7"]]
        result = list(dominance_frontier(graph, graph["12"], graph.entry))
        print(f"{result=}")

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))

    def test_dominator_algorithms(self):
        graph = make_basic_graph()

        result = list(dominance_frontier(graph, graph["A"], graph.entry))
        print(result)

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))

    def test_parallelize(self):
        graph = make_even_fib_graph()

        graph = parallelize(graph)

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))
