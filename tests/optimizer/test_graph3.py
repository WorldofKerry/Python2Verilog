import unittest

from python2verilog.ir import expressions as expr
from python2verilog.ir import graph2 as ir
from python2verilog.optimizer import graph3optimizer as opti


def make_basic_loop():
    """
    Based on slide 17 of
    https://groups.seas.harvard.edu/courses/cs153/2018fa/lectures/Lec23-SSA.pdf
    """
    x = expr.Var("x")
    y = expr.Var("y")
    z = expr.Var("z")
    a = expr.Var("a")
    n = expr.Var("n")
    m = expr.Var("m")
    ret = expr.Var("ret")

    graph = ir.CFG()

    prev = graph.add_node(
        ir.BasicBlock(
            [ir.AssignNode(x, n), ir.AssignNode(y, m), ir.AssignNode(a, expr.Int(0))]
        )
    )

    prev = ifelse = graph.add_node(
        ir.BasicBlock([ir.BranchNode(expr.BinOp(x, ">", expr.Int(0)))]), prev
    )
    prev = graph.add_node(
        ir.BasicBlock(
            [
                ir.AssignNode(a, expr.BinOp(a, "+", y)),
                ir.AssignNode(x, expr.BinOp(x, "-", expr.Int(1))),
            ]
        ),
        ifelse,
        children=[ifelse],
    )
    prev = graph.add_node(
        ir.BasicBlock([ir.AssignNode(z, expr.BinOp(a, "+", y)), ir.AssignNode(ret, z)]),
        ifelse,
    )

    return graph


def make_basic_dominance():
    """
    Based on slide 31
    https://ics.uci.edu/~yeouln/course/ssa.pdf
    """
    x = expr.Var("x")

    def asn():
        return ir.AssignNode(x, x)

    graph = ir.CFG()
    graph.unique_counter = 0

    graph.add_node(ir.BasicBlock([asn()]))
    graph.add_node(ir.BasicBlock([asn()]))
    graph.add_node(ir.BasicBlock([asn()]))
    graph.add_node(ir.BasicBlock([asn()]))
    graph.add_node(ir.BasicBlock([asn()]))
    graph.add_node(ir.BasicBlock([asn()]))
    graph.add_node(ir.BasicBlock([asn()]))
    graph.add_node(ir.BasicBlock([asn()]))

    graph.add_edge(graph[1], graph[4], graph[2])
    graph.add_edge(graph[2], graph[3])
    graph.add_edge(graph[3], graph[8])
    graph.add_edge(graph[4], graph[5], graph[6])
    graph.add_edge(graph[5], graph[3], graph[7])
    graph.add_edge(graph[6], graph[7])
    graph.add_edge(graph[7], graph[8], graph[4])

    return graph


class TestGraph3(unittest.TestCase):
    def test_graph3_0(self):
        graph = make_basic_loop()

        graph = opti.insert_phis.debug(graph).one_block(graph[2])
        # print(f"{list(opti.insert_phis.debug(graph).get_operations_lhs(graph[2]))=}")

        graph = opti.rename_blocks.debug(graph).apply(graph.dope_entry_hehe)

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape()))

    def test_graph3_1(self):
        graph = make_basic_dominance()

        graph = opti.insert_phis.debug(graph).one_block(graph[2])
        # print(f"{list(opti.insert_phis.debug(graph).get_operations_lhs(graph[2]))=}")
        # print(f"{graph.dominator_tree()}")

        graph = opti.rename_blocks.debug(graph).apply(graph.dope_entry_hehe)

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape()))
