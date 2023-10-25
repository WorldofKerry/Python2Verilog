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
        return self

    def single(self, node: ir.Element):
        parents = list(self.immediate_successors(node))
        if len(parents) <= 1:
            return
        for parent in parents:
            self.adj_list[parent] -= {node}
        self.add_node(ir.JoinNode(), *parents, children=[node])

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
            self.add_node(ir.JoinNode(), node, children=[child])
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
                    assert guard(d, ir.JoinNode)

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

    def apply(self):
        return self

    def starter(self, node: ir.Element):
        if node == self.entry:
            mapping_stack = self.entry_mapping()
            if isinstance(node, ir.AssignNode):
                node.rvalue = backwards_replace(
                    node.rvalue, self.make_mapping(mapping_stack)
                )
                new_lvalue = self.new_var(node.lvalue)
                mapping_stack[
                    self.search_mapping_and_mutate(mapping_stack, node.lvalue)
                ].append(new_lvalue)
                node.lvalue = new_lvalue
            self.inner(node, mapping_stack)
        elif isinstance(node, ir.JoinNode):
            mapping_stack = self.join_mapping(node)
            for child in self.adj_list[node]:
                self.inner(child, mapping_stack)

        return self

    def inner(self, node: ir.Element, mapping_stack: dict[expr.Var, list[expr.Var]]):
        if node in self.visited:
            return self
        self.visited.add(node)

        print(f"Inner {node=} {mapping_stack=}")

        for child in self.adj_list[node]:
            self.replace(child, mapping_stack)

        for succ in self.visit_succ(node):
            assert guard(succ, ir.JoinNode)
            # print(f"{succ=} {mapping_stack=}")
            for key, value in mapping_stack.items():
                if key not in succ.phis:
                    continue
                # print(f"{key=} {value=}")
                aliases = succ.phis.get(key, [])
                aliases.append(value[-1])
                succ.phis[key] = aliases
                # print(f"{succ.phis[key]=}")

        for join in self.visit_succ(node):
            self.inner(join, mapping_stack)

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
        for key, value in mapping_stack.items():
            if var in value:
                return key
        mapping_stack[var] = []
        return var
        raise RuntimeError(f"{var=} {mapping_stack=}")

    def replace(self, node: ir.Element, mapping_stack: dict[expr.Var, list[expr.Var]]):
        assert isinstance(mapping_stack, dict)
        for key, value in mapping_stack.items():
            assert isinstance(key, expr.Var)
            assert isinstance(value, list)

        print(f"Replace {node=} {mapping_stack=}")

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

    def visit_succ(self, node: ir.Element, visited: Optional[set[ir.Element]] = None):
        if visited is None:
            visited = set()
        if node in visited:
            return
        visited.add(node)
        for child in self.adj_list[node]:
            if isinstance(child, ir.JoinNode):
                yield child
            else:
                yield from self.visit_succ(child, visited)

    def join_mapping(self, node: ir.JoinNode):
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


class rename(Transformer):
    """
    Renames variables for SSA
    """

    def __init__(self, graph: ir.CFG, *, apply: bool = True):
        super().__init__(graph, apply=apply)
        self.visited = set()
        self.counter = 0

    def apply(self):
        self.rename(self.entry, self.initial_mapping())
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

    def initial_mapping(self):
        vars = self.get_global_variables()
        return {var: [self.new_var(var)] for var in vars}

    def new_var(self, var: expr.Var):
        var = expr.Var(f"{var.py_name}_{self.counter}")
        self.counter += 1
        return var

    def backwards_replace(
        self, expression: expr.Expression, mapping: dict[expr.Var, list[expr.Var]]
    ):
        assert isinstance(expression, expr.Expression)
        assert isinstance(mapping, dict)
        for key, value in mapping.items():
            assert isinstance(key, expr.Var)
            assert isinstance(value, list)
            for v in value:
                assert isinstance(v, expr.Var)

        expression = copy.deepcopy(expression)
        if isinstance(expression, expr.Var):
            for key in mapping:
                if key.to_string() == expression.to_string():
                    assert isinstance(mapping[key][-1], expr.Expression)
                    return mapping[key][-1]
        elif isinstance(expression, (expr.UInt, expr.Int)):
            return expression
        elif isinstance(expression, (expr.BinOp, expr.UBinOp)):
            expression.left = self.backwards_replace(expression.left, mapping)
            expression.right = self.backwards_replace(expression.right, mapping)
            return expression
        else:
            raise TypeError(f"{type(expression)} {expression}")
        return expression

    def rename(self, node: ir.Element, stack_mapper: dict[expr.Var, list[expr.Var]]):
        assert isinstance(node, ir.Element)
        assert isinstance(stack_mapper, dict)
        for key, value in stack_mapper.items():
            assert isinstance(key, expr.Var)
            assert isinstance(value, list)
            for v in value:
                assert isinstance(v, expr.Var)

        print(f"{stack_mapper=}")
        if isinstance(node, ir.AssignNode):
            node.rvalue = self.backwards_replace(node.rvalue, stack_mapper)
            new_var = self.new_var(node.lvalue)
            print(f"AssignNode {new_var=}")

            old_mapper = stack_mapper.get(node.lvalue, [])
            old_mapper.append(new_var)
            stack_mapper[node.lvalue] = old_mapper

            node.lvalue = new_var
        if isinstance(node, ir.BranchNode):
            node.expression = self.backwards_replace(node.expression, stack_mapper)
            print(f"{node=}")
        if isinstance(node, ir.JoinNode):
            print(f"join {node=} {stack_mapper=}")
            new_phis = {}
            for key, value in node.phis.items():
                new_key = self.new_var(key)
                print(f"JoinNode {new_key=}")
                value.update({self.backwards_replace(key, stack_mapper): None})
                new_phis[new_key] = value

                old_mapper = stack_mapper.get(key, [])
                old_mapper.append(new_key)
                stack_mapper[key] = old_mapper

            node.phis = new_phis
        children = dominator_tree(self).get(node, set())
        for child in children:
            self.rename(child, stack_mapper)
        print(f"{stack_mapper=}")

        # if isinstance(node, ir.JoinNode):
        #     for var in node.phis:
        #         stack_mapper[var].pop()
        # if isinstance(node, ir.AssignNode):
        #     stack_mapper[node.lvalue].pop()

        # new_phis = {}
        # for key, value in node.phis.items():
        #     value.update({self.backwards_replace(key, stack_mapper): None})
        #     stack_mapper[key].pop()


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
        dominance_ = dominance(self)
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
