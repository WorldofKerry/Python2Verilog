"""
Graph 2 optimizers
"""
import copy
import itertools
import logging
from typing import Any, Iterator, Optional

import python2verilog.ir.expressions as expr
import python2verilog.ir.graph2 as ir
from python2verilog.utils.generics import pretty_dict
from python2verilog.utils.typed import guard  # nopycln: import


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


def visit_clocked(
    graph: ir.CFG, node: ir.Element, visited: Optional[set[ir.Element]] = None
):
    """
    Recursively visit children of node that are clock nodes

    Excludes node if it is a clock node
    """
    if visited is None:
        visited = set()
    if node in visited:
        return
    visited.add(node)
    for child in graph[node]:
        if isinstance(child, ir.ClockNode):
            yield child
        else:
            yield from visit_clocked(graph, child, visited)


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
    Gets dominator frontier of n with respect to graph entry

    DF(N) = {Z | M→Z & (N dom M) & ¬(N sdom Z)}

    for Z, M, N in set of Nodes
    """
    dominance_ = dominance(graph, entry)

    zs = graph.adj_list.keys()
    ms = graph.adj_list.keys()

    for z in zs:
        for m in ms:
            # M -> Z
            m_to_z = z in graph.adj_list[m]

            # N dom M
            n_dom_m = m in dominance_[n]

            # ~(N sdom Z)
            n_sdom_z = z in dominance_[n] and n != z

            if m_to_z and n_dom_m and not n_sdom_z:
                yield z
            else:
                logging.debug(
                    f"{dominance_frontier.__name__} {z=} {m=} {m_to_z=} {n_dom_m=} {n_sdom_z=}"
                )


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


def assigned_variables(elements: Iterator[ir.Element]):
    """
    Yields variables assigned in elements
    """
    for elem in elements:
        if isinstance(elem, ir.AssignNode):
            yield elem.lvalue


class parallelize(ir.CFG):
    """
    parallelize nodes without branches
    """

    def __init__(self, graph: ir.CFG):
        self.mimic(graph)
        self.parallelize()
        pass

    def parallelize(self):
        """
        Parallelize
        """
        for first, second in self.get_pairs():
            # print(f"{first=} {second=}")
            if (
                first in self.adj_list
                and second in self.adj_list
                and first is not self.entry
                and second is not self.entry
            ):
                self.can_optimize(first, second)

    def get_pairs(self):
        """
        Get pairs of clock nodes where first dominates second
        """
        clock_nodes = filter(
            lambda x: isinstance(x, ir.ClockNode), self.adj_list.keys()
        )
        dominance_ = dominance(self, self.entry)
        for first, second in itertools.permutations(clock_nodes, 2):
            if second in dominance_[first]:
                yield first, second

    def can_optimize(self, first: ir.ClockNode, second: ir.ClockNode):
        """ """
        # if "2" not in first.unique_id or "8" not in second.unique_id:
        #     return
        print(f"{first=} {second=}")

        first_vars = set(assigned_variables(visit_nonclocked(self, first)))
        second_vars = set(assigned_variables(visit_nonclocked(self, second)))

        # print(f"{first_vars.isdisjoint(second_vars)=}")

        result = self.reattach_to_valid_parent(first, second)

    def reattach_to_valid_parent(self, first: ir.ClockNode, second: ir.ClockNode):
        """
        Attaches the children of first to second, while considering branching nodes
        """

        parents = list(self.find_valid_parent(second))

        print(f"{parents=}")

        for parent in parents:
            print(f"set one {parent=}")
            self.adj_list[parent] |= self.adj_list[second]

        next_clock_nodes = set(visit_clocked(self, second))
        print(next_clock_nodes)

        for parent in self.immediate_successors(second):
            print(f"set two {parent=}")
            if not isinstance(parent, (ir.ClockNode, ir.FalseNode, ir.TrueNode)):
                self.adj_list[parent] |= next_clock_nodes

        del self[second]

    def find_valid_parent(self, node: ir.ClockNode):
        """
        Yields valid parents
        """
        for parent in self.immediate_successors(node):
            if isinstance(parent, (ir.ClockNode, ir.FalseNode, ir.TrueNode)):
                yield parent
            else:
                yield from self.find_valid_parent(parent)
