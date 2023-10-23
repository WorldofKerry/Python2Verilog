"""
Graph 2 optimizers
"""
from typing import Iterator

import python2verilog.ir.graph2 as ir  # nopycln: import
import python2verilog.ir.expressions as expr  # nopycln: import


def get_variables(exp: expr.Expression) -> Iterator[expr.Var]:
    """
    Gets variables from expression
    """
    if isinstance(exp, expr.UBinOp):
        yield from get_variables(exp.left)
        yield from get_variables(exp.right)
    elif isinstance(exp, expr.UnaryOp):
        yield from get_variables(exp.expr)
    elif isinstance(exp, expr.Var):
        yield exp
    elif isinstance(exp, (expr.UInt, expr.Int)):
        pass
    else:
        raise RuntimeError(f"{type(exp)}")


def visit_nonclocked(graph: ir.Graph, node: ir.Element) -> Iterator[ir.Element]:
    """
    Recursively visit childrens of node,

    yielding nodes with edges to a Clock node
    """
    if any(map(lambda x: isinstance(x, ir.ClockNode), graph[node])):
        yield node
        return
    for child in graph[node]:
        yield from visit_nonclocked(graph, child)


# def is_mergeable(graph, node1: ir.Element, node2: ir.Element):
#     """
#     Merge
#     """
#     node1_
