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


class TestGraph3(unittest.TestCase):
    def test_main(self):
        graph = make_basic_loop()

        graph = opti.insert_phis.debug(graph).one_block(graph[2])
        # print(f"{list(opti.insert_phis.debug(graph).get_operations_lhs(graph[2]))=}")

        graph = opti.rename_blocks.debug(graph).apply(graph[1])

        with open("graph2_cytoscape.log", mode="w") as f:
            f.write(str(graph.to_cytoscape(id_in_label=True)))
