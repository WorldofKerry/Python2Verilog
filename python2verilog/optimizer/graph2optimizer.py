"""
Graph 2 optimizers
"""
import copy
import itertools
from abc import abstractmethod
from typing import Any, Iterator, Optional

import python2verilog.ir.expressions as expr
import python2verilog.ir.graph2 as ir
from python2verilog.ir.graph2 import *
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


def dom(graph: ir.CFG, a: ir.Element, b: ir.Element):
    """
    a dom b
    """
    dominance_ = graph.dominance()
    return b in dominance_[a]


def join_dominator_tree(graph: ir.CFG):
    """
    Dominator tree with only join nodes
    """
    graph = copy.deepcopy(newrename(graph))
    replacements = {}

    def rec(node: ir.Element):
        successors = set(graph.visit_succ(node))
        print(f"join dom tree {node=} {successors=}")
        replacements[node] = successors
        for successor in successors:
            rec(successor)

    assert guard(graph.entry, ir.BlockHeadNode)
    rec(graph.entry)

    for key, value in replacements.items():
        graph.adj_list[key] = value

    return graph.dominator_tree()


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
        self.copy(graph)
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


class add_merge_heads(Transformer):
    """
    Adds block heads when there is a merge

    Makes entry a join node
    """

    def apply(self):
        nodes = list(self.dfs(self.entry))
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


class add_block_heads(Transformer):
    """
    Add block nodes (think of it as a label)
    """

    def apply(self):
        nodes = list(self.dfs(self.entry))
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
        vars = assigned_variables(self.dfs(self.entry))
        for var in vars:
            self.apply_to_var(var)
        return self

    def apply_to_var(self, v: expr.Var):
        worklist: set[ir.Element] = set()
        ever_on_worklist: set[ir.Element] = set()
        already_has_phi: set[ir.Element] = set()

        for node in self.dfs(self.entry):
            if isinstance(node, ir.AssignNode):
                print(f"{node.lvalue=} {v=} {node.lvalue == v}")
                if node.lvalue == v:
                    worklist.add(node)

        print(f"{worklist=}")

        ever_on_worklist |= worklist

        while worklist:
            n = worklist.pop()
            for d in self.dominance_frontier(n):
                if d not in already_has_phi:
                    assert guard(d, ir.BlockHeadNode)

                    # phi = d.phis.get(v, [])
                    # phi.append(v)
                    # d.phis[v] = [v] * len(list(self.immediate_successors(d)))
                    d.phis[v] = {}

                    already_has_phi.add(d)
                    if d not in ever_on_worklist:
                        worklist.add(d)
                        ever_on_worklist.add(d)
        return self


class newrename(Transformer):
    """
    Renames variables for SSA
    """

    def __init__(self, graph: CFG, *, apply: bool = True):
        super().__init__(graph, apply=apply)
        self.visited = set()
        self.var_counter = {}
        self.stacks: dict[expr.Var, list[expr.Var]] = {}

    def apply(self, block: BasicBlock, recursion: bool = True):
        self.rename(b=block, recursion=recursion)
        return self

    def rename(self, b: BlockHeadNode, recursion: bool = True):
        """
        Based on slide 33 of
        https://ics.uci.edu/~yeouln/course/ssa.pdf
        """
        if b in self.visited:
            return
        self.visited.add(b)
        print(f"rename {b=}")

        assert guard(b, BlockHeadNode)
        self.update_phi_lhs(b)

        for stmt in self.traverse_until(b, BlockHeadNode):
            self.update_lhs_rhs_stack(stmt)

        for s in self.traverse_successors(b, BlockHeadNode):
            # For each successor in CFG
            assert guard(s, BlockHeadNode)
            for var, phi in s.phis.items():
                phi[b] = self.stacks[self.get_original_var(var)][-1]
            print(f"{b=} {str(s)=}")

        # DFS in dominator tree
        if recursion is True:
            for s in self.dominator_tree_iterate():
                if s in set(self.traverse_successors(b, BlockHeadNode)):
                    print(f"visiting {s=}")
                    self.rename(s)
        else:
            if recursion:
                cur = recursion.pop()
                self.rename(cur, recursion)
            # else:
            #     print(f"returning {self.stacks=}")
            #     return

        # Unwind stack
        counter = {}
        for key in b.phis:
            og_var = self.get_original_var(key)
            counter[og_var] = counter.get(og_var, 0) + 1
        for stmt in self.traverse_until(b, BlockHeadNode):
            if isinstance(stmt, ir.AssignNode):
                og_var = self.get_original_var(stmt.lvalue)
                counter[og_var] = counter.get(og_var, 0) + 1
        for og_var, count in counter.items():
            for _ in range(count):
                self.stacks[og_var].pop()

        print(f"Unwound {self.stacks=}")

    def get_original_var(self, var: expr.Var):
        """
        Given a value in mapping stack, gets key
        """
        if var in self.stacks:
            return var
        for key, value in self.stacks.items():
            if var in value:
                return key
        raise RuntimeError(f"{type(var)=} {var=} {self.stacks}")

    def update_phi_lhs(self, block: BlockHeadNode):
        replacement = {}
        for v, phis in block.phis.items():
            vn = self.gen_name(v)
            replacement[vn] = phis
        block.phis = replacement

    def update_lhs_rhs_stack(self, statement: Element):
        if isinstance(statement, AssignNode):
            statement.rvalue = backwards_replace(
                statement.rvalue, self.make_mapping(self.stacks)
            )
            statement.lvalue = self.gen_name(statement.lvalue)
        if isinstance(statement, BranchNode):
            statement.expression = backwards_replace(
                statement.expression, self.make_mapping(self.stacks)
            )

    def gen_name(self, var: expr.Var):
        # Make new unqiue name
        count = self.var_counter.get(var, 0)
        new_var = expr.Var(f"{var.py_name}{count}")
        self.var_counter[var] = count + 1

        # Update var stack
        stack = self.stacks.get(var, [])
        stack.append(new_var)
        self.stacks[var] = stack

        return new_var

    def make_mapping(self, mapping_stack: dict[expr.Var, list[expr.Var]]):
        """
        Converts mapping stacks to mapping

        e.g. for an item a -> [x, y, z], the resulting mapping has a -> z
        """
        return {key: value[-1] for key, value in mapping_stack.items()}


class blockify(Transformer):
    """
    Extracts block nodes from graph and their relationships
    """

    def apply(self):
        for key in self.adj_list:
            if isinstance(key, ir.BlockHeadNode):
                self.adj_list[key] = set()

        return super().apply()
