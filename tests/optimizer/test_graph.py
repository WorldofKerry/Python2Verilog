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
    visit_nonclocked,
)


class TestGraph(unittest.TestCase):
    def test_graph2(self):
        def make_graph():
            """
            Even fib numbers
            """

            out = Var("out")
            i = Var("i")
            n = Var("n")
            a = Var("a")
            b = Var("b")

            graph = CFG()

            root = graph.add_node(AssignNode(i, Int(0)))
            graph.entry = root
            prev = root

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
            return graph, root

        graph, root = make_graph()
        logging.error(graph)
        logging.error(root)

        nonclocked = list(visit_nonclocked(graph, graph["7"]))
        logging.error(nonclocked)

        nonclocked = list(visit_nonclocked(graph, graph["11"]))
        logging.error(nonclocked)

        a_copy = copy.deepcopy(graph)
        a_copy.adj_list[root] = {}
        logging.error(a_copy)

        result = dominance_frontier(graph, graph["1"], graph.entry)
        print(result)

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))
