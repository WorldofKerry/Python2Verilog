import logging
import unittest

import networkx as nx
from matplotlib import pyplot as plt

from python2verilog.ir.expressions import *  # nopycln: import
from python2verilog.ir.graph2 import *
from python2verilog.optimizer.graph2optimizer import (  # nopycln: import
    Transformer,
    codegen,
    insert_merge_nodes,
    insert_phis,
    lower_to_fsm,
    make_nonblocking,
    make_single_end_per_subgraph,
    make_ssa,
    parallelize,
    propagate_vars_and_consts,
    replace_merge_with_call_and_func,
    rmv_argless_calls,
    rmv_dead_assigns_and_params,
    rmv_loops,
    rmv_redundant_branches,
)
from python2verilog.utils.cytoscape import run_dash


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

    yiel = Var("yield")
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
        prev = graph.add_node(AssignNode(a, Int(0)))
        prev = graph.add_node(AssignNode(b, Int(1)), prev)
        prev = graph.add_node(AssignNode(i, Int(0)), prev)

    prev = if_i_lt_n_prev = graph.add_node(BranchNode(BinOp(i, "<", n)), prev)

    prev = graph.add_node(FalseNode(), if_i_lt_n_prev)
    prev = graph.add_node(ReturnNode([]), prev)

    prev = graph.add_node(TrueNode(), if_i_lt_n_prev)
    if_a_mod_2 = graph.add_node(BranchNode(Mod(a, Int(2))), prev)

    prev = graph.add_node(TrueNode(), if_a_mod_2)
    # prev = graph.add_node(AssignNode(a, BinOp(a, "+", Int(10))), prev)
    out_node = graph.add_node(YieldNode([a]), prev)

    prev = graph.add_node(FalseNode(), if_a_mod_2)

    prev = graph.add_node(AssignNode(temp, BinOp(a, "+", b)), prev, out_node)
    prev = graph.add_node(AssignNode(a, b), prev)
    prev = graph.add_node(AssignNode(b, temp), prev)

    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(
        AssignNode(i, BinOp(i, "+", Int(1))),
        prev,
    )

    graph.add_edge(prev, if_i_lt_n_prev)

    return graph


def make_seq_multiplier():
    """
    Multiplier
    """
    i = Var("i")
    n = Var("n")
    a = Var("a")
    b = Var("b")
    c = Var("c")

    graph = CFG()

    prev = graph.add_node(AssignNode(i, Int(0)))
    prev = graph.add_node(AssignNode(c, Int(0)), prev)

    prev = ifelse = graph.add_node(BranchNode(BinOp(i, "<", a)), prev)

    prev = graph.add_node(FalseNode(), ifelse)
    out_node = graph.add_node(TermNode([c]), prev)

    prev = graph.add_node(TrueNode(), ifelse)

    prev = graph.add_node(AssignNode(c, BinOp(c, "+", b)), prev)
    prev = graph.add_node(AssignNode(i, BinOp(i, "+", Int(1))), prev, children=[ifelse])

    return graph


def make_range():
    i = Var("i")
    n = Var("n")

    graph = CFG()

    prev = graph.add_node(AssignNode(i, Int(0)))

    prev = ifelse = graph.add_node(BranchNode(BinOp(i, "<", n)), prev)

    prev = graph.add_node(FalseNode(), ifelse)
    graph.add_node(TermNode([]), prev)

    prev = graph.add_node(TrueNode(), ifelse)
    prev = graph.add_node(TermNode([i]), prev)
    prev = graph.add_node(TermNode([BinOp(i, "+", Int(1))]), prev)
    prev = graph.add_node(AssignNode(i, BinOp(i, "+", Int(2))), prev, children=[ifelse])

    return graph


def make_basic_path():
    a = Var("a")
    b = Var("b")
    c = Var("c")

    i = Var("i")

    graph = CFG()

    prev = graph.add_node(AssignNode(i, i))
    prev = graph.add_node(AssignNode(a, BinOp(b, "+", Int(1))), prev)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(c, BinOp(a, "+", Int(2))), prev)

    prev = graph.add_node(MergeNode(), prev)

    return graph


def make_basic_branch():
    i = Var("i")
    n = Var("n")

    graph = CFG()

    prev = graph.add_node(AssignNode(i, Int(0)))
    prev = ifelse = graph.add_node(BranchNode(BinOp(i, "<", n)), prev)

    prev = postifelse = graph.add_node(AssignNode(n, i))
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, Int(10)), prev)
    prev = graph.add_node(TermNode([i]), prev)

    prev = graph.add_node(TrueNode(), ifelse)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, Int(1)), prev)
    prev = graph.add_node(AssignNode(i, Int(2)), prev)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, Int(3)), prev, children=[postifelse])

    prev = graph.add_node(FalseNode(), ifelse)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, Int(1)), prev)
    prev = graph.add_node(AssignNode(i, Int(2)), prev)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, i), prev)
    prev = graph.add_node(AssignNode(i, Int(4)), prev, children=[postifelse])

    return graph


def make_chain():
    a = Var("a")
    b = Var("b")
    c = Var("c")
    d = Var("d")

    graph = CFG()

    prev = graph.add_node(AssignNode(c, d))
    prev = graph.add_node(AssignNode(b, c), prev)
    prev = graph.add_node(AssignNode(a, b), prev)
    # prev = graph.add_node(AssignNode(c, BinOp(a, "+", Int(1))), prev)
    prev = graph.add_node(AssignNode(c, a), prev)
    prev = graph.add_node(TermNode([c]), prev)

    return graph


def make_const_loop():
    x = Var("x")
    i = Var("i")

    graph = CFG()

    prev = graph.add_node(AssignNode(i, Int(0)))
    ifelse = graph.add_node(BranchNode(BinOp(i, "<", Int(10))), prev)

    prev = graph.add_node(TrueNode(), ifelse)
    prev = graph.add_node(AssignNode(x, BinOp(x, "+", i)), prev)
    prev = graph.add_node(AssignNode(i, BinOp(i, "+", Int(1))), prev, children=[ifelse])

    prev = graph.add_node(FalseNode(), ifelse)
    prev = graph.add_node(TermNode([x]), prev)

    return graph


def make_basic_while():
    """
    Based on slide 17 of
    https://groups.seas.harvard.edu/courses/cs153/2018fa/lectures/Lec23-SSA.pdf
    """
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
    prev = graph.add_node(AssignNode(x, BinOp(x, "-", Int(1))), prev, children=[ifelse])

    prev = graph.add_node(FalseNode(), ifelse)
    prev = graph.add_node(AssignNode(z, BinOp(a, "+", z)), prev)
    prev = graph.add_node(AssignNode(ret, z), prev)

    return graph


def make_pssa_example():
    """
        Example from https://cseweb.ucsd.edu/~calder/papers/PACT-99-PSSA.pdf

    func(a, c):
        d = c * 2
        if a > c:
            b = 7
            if b > d:
                return 123
        else:
            b = 6
            if b < d:
                a = b + 4
        c = a + b
        return c
    """
    a = Var("a")
    b = Var("b")
    c = Var("c")
    d = Var("d")

    graph = CFG()

    prev = graph.add_node(AssignNode(d, BinOp(c, "*", Int(2))))
    prev = ifelse = graph.add_node(BranchNode(BinOp(a, ">", c)), prev)

    prev = graph.add_node(TrueNode(), ifelse)
    prev = graph.add_node(AssignNode(b, Int(7)), prev)
    prev = ifelse1 = graph.add_node(BranchNode(BinOp(b, ">", d)), prev)

    prev = graph.add_node(TrueNode(), ifelse1)
    graph.add_node(ReturnNode([Int(123)]), prev)

    prev = end1 = graph.add_node(FalseNode(), ifelse1)

    prev = graph.add_node(FalseNode(), ifelse)
    prev = graph.add_node(AssignNode(b, Int(6)), prev)
    prev = ifelse1 = graph.add_node(BranchNode(BinOp(b, "<", d)), prev)

    prev = graph.add_node(TrueNode(), ifelse1)
    prev = end3 = graph.add_node(AssignNode(a, BinOp(b, "+", Int(4))), prev)

    prev = end2 = graph.add_node(FalseNode(), ifelse1)

    prev = graph.add_node(AssignNode(c, BinOp(a, "+", b)), end1, end2, end3)
    prev = graph.add_node(ReturnNode([c]), prev)

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

        result = dominance(graph, graph.dope_entry_hehe)[graph["7"]]
        result = list(dominance_frontier(graph, graph["12"], graph.dope_entry_hehe))
        print(f"{result=}")

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(use_repr=True)))

    def test_dominator_algorithms(self):
        graph = make_pdf_example()

        dom_frontier = set(graph.dominance_frontier(graph["4"]))
        # print(f"{dom_frontier=}")
        self.assertEqual({graph[3], graph[4], graph[8]}, dom_frontier)

        dom_frontier = set(graph.dominance_frontier(graph["2"]))
        # print(f"{dom_frontier=}")
        self.assertEqual({graph[3]}, dom_frontier)

        dom_tree = graph.dominator_tree()
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

    def test_metaclass(self):
        graph = make_chain()

        graph = graph | CoolTrans

        run_dash(graph.to_cytoscape())

    def test_ssa_funcs(self):
        graph = make_pssa_example()
        # graph = make_even_fib_graph_no_clocks()
        # graph = make_chain()
        # graph = make_seq_multiplier()
        # graph = make_range()
        # graph = make_basic_branch()
        # graph = make_const_loop()

        # graph = make_pdf_example()
        # graph = make_basic_while()
        # graph = make_basic_path()

        graph = (
            graph
            | insert_merge_nodes()
            | insert_phis()
            | make_ssa()
            | replace_merge_with_call_and_func()
            | propagate_vars_and_consts()
            | rmv_dead_assigns_and_params()
            | rmv_argless_calls()
            | rmv_redundant_branches()
            | rmv_dead_assigns_and_params()  # when branch references param
            # | parallelize
            # | rmv_loops
        )

        lowered = CFG()
        lowered = (
            graph
            | make_single_end_per_subgraph(threshold=1)
            # | lower_to_fsm(threshold=1)
            # | insert_merge_nodes()
            # | insert_phis()
            # | make_ssa()
            | rmv_dead_assigns_and_params()
            | rmv_argless_calls()
            | rmv_dead_assigns_and_params()
            | rmv_redundant_branches()
            | make_nonblocking()
        )
        # print(f"{type(lowered)} {lowered}")

        result = lowered | codegen()
        for entry in set(lowered.exit_to_entry.values()):
            output = list(result.start(entry))
            text = "\n".join(output).replace(".", "")
            print(f"{text}")

        # graph = rmv_assigns_and_phis.debug(graph).apply()
        # graph = rmv_redundant_calls(graph)
        # graph = rmv_redundant_branches(graph)

        # graph = dataflow.debug(graph).apply()
        # print(f"{graph.dominance()=}")

        # with open("graph2_cytoscape.log", mode="w") as f:
        # f.write(str(graph.to_cytoscape()))
        cyto = graph.to_cytoscape()
        lowered_cyto = lowered.to_cytoscape(id_prefix="lowered")
        # print(f"{lowered_cyto=}")
        cyto["nodes"].extend(lowered_cyto["nodes"])
        cyto["edges"].extend(lowered_cyto["edges"])
        # print(f"{cyto['nodes']=}")
        run_dash(cyto)
