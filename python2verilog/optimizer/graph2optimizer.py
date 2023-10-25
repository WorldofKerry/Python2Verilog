"""
Graph 2 optimizers
"""
from abc import abstractmethod
import copy
import itertools
import logging
from typing import Any, Iterator, Optional

import python2verilog.ir.expressions as expr
import python2verilog.ir.graph2 as ir
from python2verilog.optimizer.helpers import backwards_replace
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
    for child in graph[node]:
        if not isinstance(child, ir.ClockNode):
            yield child


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
    logging.debug(f"\n{print_tree(dom_tree, source)}")
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
    yield source
    for child in graph[source]:
        yield from dfs(graph, child, visited)


def assigned_variables(elements: Iterator[ir.Element]):
    """
    Yields variables assigned in elements
    """
    for elem in elements:
        if isinstance(elem, ir.AssignNode):
            yield elem.lvalue


class Transformer(ir.CFG):
    """
    Abstract bass class for graph transformers
    """

    def __init__(self, graph: ir.CFG, *, apply: bool = True):
        self.mimic(graph)
        if apply:
            self.apply()

    @classmethod
    def debug(cls, graph: ir.CFG):
        """
        A debug version that does not apply any transformations
        """
        return cls(graph=graph, apply=False)

    @abstractmethod
    def apply(self):
        """
        Apply transformation
        """
        return self


class add_join_nodes(Transformer):
    """
    Adds join nodes
    """

    def apply(self):
        nodes = list(dfs(self, self.entry))
        for node in nodes:
            self.join(node)
        return self

    def join(self, node: ir.Element):
        parents = list(self.immediate_successors(node))
        if len(parents) <= 1:
            return
        for parent in parents:
            self.adj_list[parent] -= {node}
        self.add_node(ir.JoinNode(), *parents, children=[node])

        return self


class insert_phi(Transformer):
    """
    Add Phi Nodes
    """

    def apply(self):
        vars = assigned_variables(dfs(self, self.entry))
        for var in vars:
            self.apply_to_var(var)
        return self

    def apply_to_var(self, v: expr.Var):
        worklist: set[ir.Element] = set()
        ever_on_worklist: set[ir.Element] = set()
        already_has_phi: set[ir.Element] = set()

        for node in dfs(self, self.entry):
            if isinstance(node, ir.AssignNode):
                print(f"{node.lvalue=} {v=} {node.lvalue == v}")
                if node.lvalue == v:
                    worklist.add(node)

        print(f"{worklist=}")

        ever_on_worklist |= worklist

        while worklist:
            n = worklist.pop()
            for d in dominance_frontier(self, n, self.entry):
                if d not in already_has_phi:
                    assert guard(d, ir.JoinNode)

                    phi = d.phis.get(v, {})
                    phi[n.unique_id] = None
                    d.phis[v] = phi

                    already_has_phi.add(d)
                    if d not in ever_on_worklist:
                        worklist.add(d)
                        ever_on_worklist.add(d)
        return self


class rename(Transformer):
    """
    Renames variables for SSA
    """

    def __init__(self, graph: ir.CFG, *, apply: bool = True):
        super().__init__(graph, apply=apply)
        self.visited = set()
        self.counter = -1
        self.stack: dict[expr.Var, set[expr.Var]] = self.initial_mapping()
        print(f"{self.stack=}")

    def apply(self):
        self.rename(self.entry)
        return self

    def initial_mapping(self):
        vars = assigned_variables(dfs(self, self.entry))
        return {var: self.new_var() for var in vars}

    def new_var(self):
        var = expr.Var(f"v{self.counter}")
        self.counter += 1
        return var

    def rename(self, b: ir.Element):
        if b in self.visited:
            return
        if isinstance(b, ir.JoinNode):
            for var in b.phis:
                v = var
                del b.phis[v]
                vn = self.new_var()
                b.phis[vn] = []
        if isinstance(b, ir.AssignNode):
            b.rvalue = backwards_replace(b.rvalue, self.stack)
            vn = self.new_var()
            b.lvalue = vn
        for s in self[b]:
            print(f"{s=}")


class make_ssa(Transformer):
    """
    Make CFG use ssa
    """

    def __init__(self, graph: ir.CFG, *, apply: bool = True):
        super().__init__(graph, apply=apply)
        self.variables: dict[expr.Var, set[expr.Var]] = {}
        self.counter = 0

    def apply(self):
        """
        Run
        """
        self.visit(
            self.entry,
            set(),
            {var: self.new_var() for var in self.get_global_variables()},
        )

        print(f"{self.variables=}")

        return self

    def get_global_variables(self):
        nodes = dfs(self, self.entry)
        lhs_vars = set()
        global_vars = set()
        for node in nodes:
            if isinstance(node, ir.AssignNode):
                global_vars |= set(get_variables(node.rvalue)) - lhs_vars
                lhs_vars |= set(get_variables(node.lvalue))
        return global_vars

    def new_var(self):
        """
        New SSA var
        """
        new_var = expr.Var(f"v{self.counter}")
        self.counter += 1
        return new_var

    def get_var_usage(self, node: ir.Element, var: expr.Var):
        """
        Get var uage
        """
        for value in self.variables.values():
            if var in value:
                subset = value

        print(f"{subset=}")

        nodes = dfs(self, node)

    def visit(
        self,
        node: ir.Element,
        visited: set[ir.Element],
        mapping: dict[expr.Var, expr.Expression],
    ):
        for key, value in mapping.items():
            if key not in self.variables:
                self.variables[key] = set()
            self.variables[key].add(value)

        print(f"{node=} {mapping=}")
        if node in visited:
            return
        visited.add(node)

        if isinstance(node, ir.AssignNode):
            node.rvalue = backwards_replace(node.rvalue, mapping)

            new_var = expr.Var(f"v{self.counter}")
            self.counter += 1

            mapping[node.lvalue] = new_var

            node.lvalue = new_var

            print(f"post {node=} {mapping=}")

        if isinstance(node, ir.BranchNode):
            node.expression = backwards_replace(node.expression, mapping)

        for child in self.adj_list[node]:
            self.visit(child, visited, copy.deepcopy(mapping))

        return self


class parallelize(ir.CFG):
    """
    parallelize nodes without branches
    """

    def __init__(self, graph: ir.CFG):
        self.mimic(graph)

    def run(self):
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

        # print(f"FRESSSSH")
        # self.can_optimize(self.entry, self["2"])
        return self

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
        # if "11" not in first.unique_id or "13" not in second.unique_id:
        #     return
        print(f"{first=} {second=}")

        if len(self.adj_list[second]) == 0:
            print("Skipped second has no children")
            return self

        first_nonclocked = list(visit_nonclocked(self, first))
        second_nonclocked = list(visit_nonclocked(self, second))

        print(f"{first_nonclocked=} {second_nonclocked=}")

        first_vars = set(assigned_variables(first_nonclocked))
        second_vars = set(assigned_variables(second_nonclocked))

        print(f"{first_vars.isdisjoint(second_vars)=} {first_vars=} {second_vars=}")

        if first_vars.isdisjoint(second_vars):
            self.reattach_to_valid_parent(first, second)

        return self

    def reattach_to_valid_parent(self, first: ir.ClockNode, second: ir.ClockNode):
        """
        Attaches the children of first to second, while considering branching nodes
        """

        foster_parents = list(self.find_valid_parent(second))

        print(f"{foster_parents=}")

        orphans = self[second]

        print(f"{orphans=}")

        sad_parents = list(self.immediate_successors(second))

        print(f"{sad_parents=}")

        adopted_children = list(visit_clocked(self, second))

        print(f"{adopted_children=}")

        for foster_parent in foster_parents:
            self.adj_list[foster_parent] |= orphans

        for sad_parent in sad_parents:
            self.adj_list[sad_parent] |= set(adopted_children)

        # for parent in foster_parents:
        #     print(f"set one {parent=}")
        #     self.adj_list[parent] |= self.adj_list[second]

        # next_clock_nodes = set(visit_clocked(self, second))
        # print(next_clock_nodes)

        # for parent in self.adj_list[second]:
        #     print(f"set two {parent=}")
        #     self.adj_list[parent] |= next_clock_nodes

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
