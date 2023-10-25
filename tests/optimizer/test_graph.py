import logging
import unittest

import networkx as nx
from matplotlib import pyplot as plt

from python2verilog.ir.expressions import *  # nopycln: import
from python2verilog.ir.graph2 import *
from python2verilog.optimizer.graph2optimizer import (  # nopycln: import
    add_block_nodes,
    add_join_nodes,
    dfs,
    dominance,
    dominance_frontier,
    dominator_tree,
    insert_phi,
    make_ssa,
    newrename,
    parallelize,
    rename,
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

    # clock node vs first node as root
    if False:
        root = graph.add_node(ClockNode())
        prev = graph.add_node(AssignNode(i, Int(0)), root)
    else:
        root = prev = graph.add_node(AssignNode(i, Int(0)))

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
    out = Var("out")
    i = Var("i")
    n = Var("n")
    a = Var("a")
    b = Var("b")

    graph = CFG()
    prev = graph.add_node(ClockNode())
    prev = graph.add_node(AssignNode(out, Int(10)), prev)

    prev = graph.add_node(ClockNode(), prev)
    prev = graph.add_node(BranchNode(BinOp(a, "<", b)), prev)
    true = graph.add_node(TrueNode(), prev)
    false = graph.add_node(FalseNode(), prev)

    prev = graph.add_node(ClockNode(), true)
    prev = graph.add_node(AssignNode(out, Int(11)), prev)

    prev = graph.add_node(ClockNode(), prev)
    prev = graph.add_node(AssignNode(out, Int(12)), prev)
    tail1 = graph.add_node(ClockNode(), prev)

    prev = graph.add_node(ClockNode(), false)
    prev = graph.add_node(AssignNode(out, Int(13)), prev)

    prev = graph.add_node(ClockNode(), prev)
    prev = graph.add_node(AssignNode(i, Int(14)), prev)
    tail2 = graph.add_node(ClockNode(), prev)

    prev = graph.add_node(AssignNode(n, Int(789)), tail1, tail2)
    graph.add_node(ClockNode(), prev)

    return graph


def make_even_fib_graph_no_clocks():
    """
    Even fib numbers
    """

    out = Var("out")
    i = Var("i")
    n = Var("n")
    a = Var("a")
    b = Var("b")
    temp = Var("temp")

    graph = CFG()

    # clock node vs first node as root
    if False:
        root = graph.add_node(ClockNode())
        prev = graph.add_node(AssignNode(i, Int(0)), root)
    else:
        root = prev = graph.add_node(AssignNode(i, Int(0)))

    prev = if_i_lt_n_prev = graph.add_node(BranchNode(BinOp(i, "<", n)), prev)

    prev = graph.add_node(TrueNode(), prev)
    if_a_mod_2 = graph.add_node(BranchNode(Mod(a, Int(2))), prev)
    prev = graph.add_node(TrueNode(), if_a_mod_2)
    prev = graph.add_node(AssignNode(out, a), prev)

    prev = graph.add_node(AssignNode(temp, BinOp(a, "+", b)), prev)
    graph.add_node(FalseNode(), if_a_mod_2, children=[prev])
    prev = graph.add_node(AssignNode(a, b), prev)
    prev = graph.add_node(AssignNode(b, temp), prev)

    prev = graph.add_node(
        AssignNode(i, BinOp(i, "+", Int(1))),
        prev,
        children=[if_i_lt_n_prev],
    )
    return graph


def make_basic_branch():
    i = Var("i")
    n = Var("n")

    graph = CFG()

    prev = graph.add_node(AssignNode(i, Int(0)))
    prev = ifelse = graph.add_node(BranchNode(BinOp(i, "<", n)), prev)

    postifelse = graph.add_node(AssignNode(n, i))

    prev = graph.add_node(TrueNode(), ifelse)
    prev = graph.add_node(AssignNode(i, Int(1)), prev, children=[postifelse])

    prev = graph.add_node(FalseNode(), ifelse)
    prev = graph.add_node(AssignNode(i, Int(2)), prev, children=[postifelse])

    return graph


def make_basic_while():
    x = Var("x")
    y = Var("y")
    z = Var("z")
    a = Var("a")
    n = Var("n")
    m = Var("m")
    ret = Var("ret")

    graph = CFG()

    prev = graph.add_node(AssignNode(x, n))
    prev = graph.add_node(AssignNode(y, m), prev)
    prev = graph.add_node(AssignNode(a, Int(0)), prev)

    prev = ifelse = graph.add_node(BranchNode(BinOp(x, ">", Int(0))), prev)

    prev = graph.add_node(TrueNode(), ifelse)
    prev = graph.add_node(AssignNode(a, BinOp(a, "+", y)), prev)
    prev = graph.add_node(
        AssignNode(x, BinOp(x, "-", Int(-1))), prev, children=[ifelse]
    )

    prev = graph.add_node(FalseNode(), ifelse)
    prev = graph.add_node(AssignNode(z, BinOp(a, "+", z)), prev)
    prev = graph.add_node(AssignNode(ret, z), prev)

    return graph


def make_pdf_example():
    """
    Example from PDF "Building Static Single Assignment Form" by Yeoul NA, UCI
    """
    graph = CFG()
    graph.unique_counter = 0

    for _ in range(8):
        graph.add_node(ClockNode())

    graph.add_edge(graph[1], graph[2], graph[4])
    graph.add_edge(graph[2], graph[3])
    graph.add_edge(graph[3], graph[8])
    graph.add_edge(graph[4], graph[5], graph[6])
    graph.add_edge(graph[5], graph[3], graph[7])
    graph.add_edge(graph[6], graph[7])
    graph.add_edge(graph[7], graph[4], graph[8])

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
        graph = make_pdf_example()

        dom_frontier = set(dominance_frontier(graph, graph["4"], graph.entry))
        # print(f"{dom_frontier=}")
        self.assertEqual({graph[3], graph[4], graph[8]}, dom_frontier)

        dom_frontier = set(dominance_frontier(graph, graph["2"], graph.entry))
        # print(f"{dom_frontier=}")
        self.assertEqual({graph[3]}, dom_frontier)

        dom_tree = dominator_tree(graph)
        # print(f"{dom_tree=}")
        self.assertEqual(
            {
                graph[1]: {graph[2], graph[3], graph[4], graph[8]},
                graph[4]: {graph[5], graph[6], graph[7]},
            },
            dom_tree,
        )

        # with open("graph2_cytoscape.log", mode="w") as f:
        #     f.write(str(graph.to_cytoscape(id_in_label=True)))

    def test_parallelize(self):
        graph = make_even_fib_graph()

        graph = parallelize(graph).run()

        dom_frontier = list(dominance_frontier(graph, graph["12"], graph.entry))
        print(f"{dom_frontier=}")

        dom_frontier = list(dominance_frontier(graph, graph["0"], graph.entry))
        print(f"{dom_frontier=}")

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))

    def test_make_ssa(self):
        graph = make_even_fib_graph()

        graph = make_ssa(graph).run()

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))

    def test_make_clockless(self):
        graph = make_even_fib_graph_no_clocks()

        graph = make_ssa(graph).run()

        dom_frontier = list(dominance_frontier(graph, graph["8"], graph.entry))
        print(f"{dom_frontier=}")

        dom_frontier = list(dominance_frontier(graph, graph["9"], graph.entry))
        print(f"{dom_frontier=}")

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))

    def test_ssa_funcs(self):
        # graph = make_even_fib_graph_no_clocks()
        # graph = make_basic_branch()
        graph = make_basic_while()

        graph = add_join_nodes.debug(graph).apply()
        graph = add_block_nodes.debug(graph).apply()
        graph = insert_phi.debug(graph).apply()
        # graph = newrename.debug(graph).single(graph.entry)
        graph = newrename.debug(graph).single(graph[10])

        dom_frontier = list(dominance_frontier(graph, graph[2], graph.entry))
        print(f"{dom_frontier=}")

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))
