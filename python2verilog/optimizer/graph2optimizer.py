"""
Graph 2 optimizers
"""
import copy
import itertools
import logging
from abc import abstractmethod
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


def dominance(graph: ir.CFG) -> dict[ir.Element, set[ir.Element]]:
    """
    Returns dict dominance relations,

    i.e. k in ret[n] means n dominates k
    """
    vertices = set(dfs(graph, graph.entry))
    dominance_ = {}

    for vertex in vertices:
        temp_graph = copy.deepcopy(graph)
        del temp_graph[vertex]
        new_vertices = set(dfs(temp_graph, graph.entry))
        delta = vertices - new_vertices
        dominance_[vertex] = delta
    # logging.debug(f"\n{print_tree(dominance_, graph.entry)}")
    return dominance_


def dom(graph, a: ir.Element, b: ir.Element):
    """
    a dom b
    """
    dominance_ = dominance(graph)
    return b in dominance_[a]


def dominator_tree(graph: ir.CFG):
    """
    Returns dict representing dominator tree
    """
    visited = set()
    nodes = reversed(list(dfs(graph, graph.entry)))
    dom_tree = {}
    dominance_ = dominance(graph)
    for node in nodes:
        temp = dominance_[node] - visited - {node}
        if len(temp) > 0:
            dom_tree[node] = temp
        visited |= temp

    # return {key.unique_id: set(map(lambda x: x.unique_id, value)) for key, value in dom_tree.items()}
    return dom_tree


def join_dominator_tree(graph: ir.CFG):
    """
    Dominator tree with only join nodes
    """
    graph = copy.deepcopy(newrename(graph))
    replacements = {}

    def rec(node: ir.Element):
        successors = set(graph.iter_block_children(node))
        print(f"join dom tree {node=} {successors=}")
        replacements[node] = successors
        for successor in successors:
            rec(successor)

    assert guard(graph.entry, ir.BlockHeadNode)
    rec(graph.entry)

    for key, value in replacements.items():
        graph.adj_list[key] = value

    return dominator_tree(graph)


def build_tree(node_dict, root):
    if root in node_dict:
        children = node_dict[root]
        tree = {root: {}}
        for child in children:
            subtree = build_tree(node_dict, child)
            tree[root].update(subtree)
        return tree
    else:
        return {root: {}}


def dominance_frontier(graph: ir.CFG, n: ir.Element, entry: ir.Element):
    """
    Gets dominator frontier of n with respect to graph entry

    DF(N) = {Z | M→Z & (N dom M) & ¬(N sdom Z)}

    for Z, M, N in set of Nodes
    """
    dominance_ = dominance(graph)

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


def iter_non_join(graph: ir.CFG, node: ir.Element):
    """
    Recursively yields the node's children,

    not going past join nodes
    """
    for child in graph[node]:
        if not isinstance(child, ir.BlockHeadNode):
            yield child
            yield from iter_non_join(graph, child)


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
            self.single(node)
        join = self.add_node(ir.BlockHeadNode(), children=[self.entry])
        self.entry = join
        return self

    def single(self, node: ir.Element):
        parents = list(self.immediate_successors(node))
        if len(parents) <= 1:
            return
        for parent in parents:
            self.adj_list[parent] -= {node}
        self.add_node(ir.BlockHeadNode(), *parents, children=[node])

        return self


class add_dumb_join_nodes(Transformer):
    """
    Add block nodes (think of it as a label)
    """

    def apply(self):
        nodes = list(dfs(self, self.entry))
        for node in nodes:
            self.single(node)
        return self

    def single(self, node: ir.Element):
        if not isinstance(node, (ir.TrueNode, ir.FalseNode)):
            return self
        children = set(self.adj_list[node])
        for child in children:
            self.add_node(ir.BlockHeadNode(), node, children=[child])
        self.adj_list[node] -= children
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
                    assert guard(d, ir.BlockHeadNode)

                    # phi = d.phis.get(v, [])
                    # phi.append(v)
                    # d.phis[v] = [v] * len(list(self.immediate_successors(d)))
                    d.phis[v] = []

                    already_has_phi.add(d)
                    if d not in ever_on_worklist:
                        worklist.add(d)
                        ever_on_worklist.add(d)
        return self


class newrename(Transformer):
    """
    Renames variables for SSA
    """

    def __init__(self, graph: ir.CFG, *, apply: bool = True):
        super().__init__(graph, apply=apply)
        self.counter = 0
        self.var_numberer = {}
        self.visited = set()
        self.phied = set()

    def apply(self):
        return self

    def starter(self, node: ir.Element):
        assert guard(node, ir.BlockHeadNode)

        mapping_stack = self.join_mapping(node)
        self.inner(node, mapping_stack)

        return self

    def inner(self, node: ir.Element, mapping_stack: dict[expr.Var, list[expr.Var]]):
        assert guard(node, ir.BlockHeadNode)

        if node in self.visited:
            print(f"Early return {node=} {mapping_stack=}")
            # Another node has this node as as a successor, but already visited,
            # This means we can just update its phis
            for key, value in node.phis.items():
                # Original variable before renaming
                og_var = self.search_mapping_and_mutate(mapping_stack, key)
                try:
                    node.phis[key].append(mapping_stack[og_var][-1])
                except:
                    print(f"Threw on {key=} {node=} {mapping_stack=}")
                    return self
            return self
        self.visited.add(node)

        # Update LHS of node's PHIs with new variable
        # Update mapping stack to mimic
        new_phis = {}
        for key, value in node.phis.items():
            new_var = self.new_var(key)
            new_phis[new_var] = value

            # Special case for temporaries
            stack = mapping_stack.get(key, [])
            stack.append(new_var)
            mapping_stack[key] = stack

        node.phis = new_phis

        # Replace variable usage on LHS and RHS
        # The top of stack should be what successors should use
        for child in self.adj_list[node]:
            self.replace(child, mapping_stack)

        # Update RHS of phi successors
        for succ in self.iter_block_children(node):
            assert guard(succ, ir.BlockHeadNode)
            for key, value in mapping_stack.items():
                if key not in succ.phis:
                    continue
                aliases = succ.phis.get(key, [])
                aliases.append(value[-1])
                succ.phis[key] = aliases

        # Do work on successors
        # Make a copy with only join nodes
        dom_tree = join_dominator_tree(self)

        print(f"{dom_tree=}")
        print(f"{dom_tree[node]=} {node=}")
        # print(f"{dom_tree[self[15]]=}")

        return self

        for join in self.iter_block_children(node):
            print(f"Pre {join=} {node=} {mapping_stack=}")

            self.inner(join, mapping_stack)

            print(f"Between {join=} {mapping_stack=} {node=}")

            non_joins = []
            for child in self.adj_list[node]:
                non_joins.extend(iter_non_join(self, node))
            print(f"{non_joins=}")
            for node in non_joins:
                if isinstance(node, ir.AssignNode):
                    og_var = self.search_mapping_and_mutate(mapping_stack, node.lvalue)
                    try:
                        mapping_stack[og_var].pop()
                    except:
                        print(f"Pop failed {node=} {mapping_stack=}")
                        return self

            print(f"Post-Unwind {join=} {mapping_stack=} {node=}")
        return self

    def make_mapping(self, mapping_stack: dict[expr.Var, list[expr.Var]]):
        """
        Converts mapping stack to mapping
        """
        return {key: value[-1] for key, value in mapping_stack.items()}

    def search_mapping_and_mutate(
        self, mapping_stack: dict[expr.Var, list[expr.Var]], var: expr.Var
    ):
        """
        Search mapping for variable and returns original key
        """
        if var in mapping_stack:
            return var
        for key, value in mapping_stack.items():
            if var in value:
                return key
        mapping_stack[var] = []
        return var

    def replace(self, node: ir.Element, mapping_stack: dict[expr.Var, list[expr.Var]]):
        assert isinstance(mapping_stack, dict)
        for key, value in mapping_stack.items():
            assert isinstance(key, expr.Var)
            assert isinstance(value, list)

        if isinstance(node, ir.AssignNode):
            node.rvalue = backwards_replace(
                node.rvalue, self.make_mapping(mapping_stack)
            )
            new_lvalue = self.new_var(node.lvalue)
            mapping_stack[
                self.search_mapping_and_mutate(mapping_stack, node.lvalue)
            ].append(new_lvalue)
            node.lvalue = new_lvalue
            for child in self.adj_list[node]:
                self.replace(child, mapping_stack)
        if isinstance(node, ir.BranchNode):
            node.expression = backwards_replace(
                node.expression, self.make_mapping(mapping_stack)
            )
            for child in self.adj_list[node]:
                self.replace(child, mapping_stack)
        if isinstance(node, (ir.TrueNode, ir.FalseNode)):
            for child in self.adj_list[node]:
                self.replace(child, mapping_stack)

    def join_mapping(self, node: ir.BlockHeadNode):
        new_phis = {}
        mapping = {}
        for var, phis in node.phis.items():
            new_var = self.new_var(var)
            mapping[var] = [new_var]
            new_phis[new_var] = phis
        node.phis = new_phis
        return mapping

    def get_global_variables(self):
        nodes = dfs(self, self.entry)
        lhs_vars = set()
        global_vars = set()
        for node in nodes:
            if isinstance(node, ir.AssignNode):
                global_vars |= set(get_variables(node.rvalue)) - lhs_vars
                lhs_vars |= set(get_variables(node.lvalue))
        return global_vars

    def entry_mapping(self):
        vars = self.get_global_variables()
        return {var: [var] for var in vars}

    def new_var(self, var: expr.Var):
        count = self.var_numberer.get(var, 0)
        new_var = expr.Var(f"{var.py_name}{count}")
        self.var_numberer[var] = count + 1
        return new_var


class blockify(Transformer):
    """
    Removes non-block nodes
    """

    def __init__(self, graph: ir.CFG, *, apply: bool = True):
        super().__init__(graph, apply=apply)
        self.visited = set()

    def apply(self):
        self.join_blocks(self.entry)
        self.remove_nonblocks()
        return self

    def join_blocks(self, node: ir.Element):
        """
        Join block nodes
        """

        if node in self.visited:
            return
        self.visited.add(node)

        if isinstance(node, ir.BlockHeadNode):
            successors = set(self.iter_block_children(node))
            print(f"{node=} {successors=}")
            for succ in successors:
                self.join_blocks(succ)
            self.adj_list[node] = successors

    def remove_nonblocks(self):
        """
        Remove non-block nodes
        """
        for node in set(self.adj_list):
            if not isinstance(node, ir.BlockHeadNode):
                del self[node]


class to_dominance(Transformer):
    """
    To dominance
    """

    def apply(self):
        self.do()
        return super().apply()

    def do(self):
        domi = dominance(self)
