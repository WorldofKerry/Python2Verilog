"""
Graph 2 optimizers
"""
import copy
import logging
from typing import Any, Iterator, Optional

import python2verilog.ir.expressions as expr
import python2verilog.ir.graph2 as ir  # nopycln: import
from python2verilog.utils.generics import pretty_dict  # nopycln: import


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


def dominator_tree(graph: ir.Graph, source: ir.Element) -> Iterator[ir.Element]:
    """
    Yields nodes that source dominates
    """
    vertices = set(dfs(graph, source))
    dom_tree = {}

    for vertex in vertices:
        temp_graph = copy.deepcopy(graph)
        del temp_graph[vertex]
        # logging.error(f"deleted {repr(vertex)}")

        # new_vertices = set(dfs(temp_graph, source)).intersection(graph[vertex])
        new_vertices = set(dfs(temp_graph, source))
        # logging.error(f"confused {graph[vertex]=} {new_vertices & graph[vertex]=}")
        # for v in graph[vertex]:
        #     logging.error(repr(v))
        # logging.error("next")
        # for v in new_vertices:
        #     logging.error(repr(v))

        # logging.error(f"{new_vertices=}")
        delta = vertices - new_vertices
        delta = delta
        # logging.error(f"{delta=}")
        dom_tree[vertex] = delta
        logging.error(f"{repr(vertex)} dominates {dom_tree[vertex]}")

    logging.error(f"\n{print_tree(dom_tree, source)}")

    return graph


def print_tree(
    tree: [Any, Any], node: Any, level: int = 0, visited: Optional[set[Any]] = None
):
    """
    Print tree stored as dict
    """
    if visited is None:
        visited = set()
    if node in visited:
        return ""
    visited.add(node)
    ret = "\t" * level + " -> " + repr(node) + "\n"
    for child in tree[node]:
        ret += print_tree(tree, child, level + 1, visited)
    return ret


def dfs(
    graph: ir.Graph, source: ir.Element, visited: Optional[set[ir.Element]] = None
) -> Iterator[ir.Element]:
    """
    Depth-first search
    """
    if visited is None:
        visited = set()
    if source in visited:
        return
    if source not in graph.adj_list:
        return
    visited.add(source)
    for child in graph[source]:
        yield from dfs(graph, child, visited)
    yield source
