"""
Graph 2 optimizers
"""
from typing import Iterator

import python2verilog.ir.graph2 as ir  # nopycln: import


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


def is_mergeable(graph):
    """
    Merge
    """
