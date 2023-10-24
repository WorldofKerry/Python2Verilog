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


def visit_nonclocked(graph: ir.CFG, node: ir.Element) -> Iterator[ir.Element]:
    """
    Recursively visit childrens of node,

    yielding nodes with edges to a Clock node
    """
    if any(map(lambda x: isinstance(x, ir.ClockNode), graph[node])):
        yield node
        return
    for child in graph[node]:
        yield from visit_nonclocked(graph, child)


def dominance(graph: ir.CFG, source: ir.Element):
    """
    Returns dict representing dominator tree of source
    """
    vertices = set(dfs(graph, source))
    dom_tree = {}

    for vertex in vertices:
        temp_graph = copy.deepcopy(graph)
        del temp_graph[vertex]
        new_vertices = set(dfs(temp_graph, source))
        delta = vertices - new_vertices
        dom_tree[vertex] = delta
    logging.error(f"\n{print_tree(dom_tree, source)}")
    return dom_tree


def dominance_frontier(graph: ir.CFG, n: ir.Element, entry: ir.Element):
    """
    Gets dominator frontier of source with respect to entry

    DF(N) = {Z | M→Z & (N dom M) & ¬(N sdom Z)}

    for Z, M, N in set of Nodes
    """
    dominance_ = dominance(graph, entry)
    for z_candidate in graph.adj_list.keys():
        # Look for canidates for Z

        # Check for N dom M
        for m_candidate in dominance_[n]:
            # Check for M -> Z
            if z_candidate in graph.adj_list[m_candidate]:
                # Check for N sdom Z
                n_sdom_Z = z_candidate in dominance_[n] and z_candidate != n
                if not n_sdom_Z:
                    yield z_candidate

    # set_of_M = dominance(graph, entry)[source]
    # source_frontier = set()
    # for M in set_of_M:
    #     source_frontier |= graph[M] & set_of_M
    # return source_frontier


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
    graph: ir.CFG, source: ir.Element, visited: Optional[set[ir.Element]] = None
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
