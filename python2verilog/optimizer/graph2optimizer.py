"""
Graph 2 optimizers
"""
import copy
import itertools
from abc import abstractmethod
import types
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

    assert guard(graph.entry, ir.BlockHead)
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
        if not isinstance(child, ir.BlockHead):
            yield child
            yield from iter_non_join(graph, child)


class TransformerMetaClass(type):
    def __ror__(self, __value: Union[ir.CFG, type[ir.CFG]]) -> ir.CFG:
        if isinstance(__value, ir.CFG):
            ret = self.__new__(self)
            ret.__init__(__value)
            return ret
        if isinstance(__value, type(Transformer)):
            return __value(graph=self)
        return NotImplemented


class Transformer(ir.CFG, metaclass=TransformerMetaClass):
    """
    Abstract bass class for graph transformers
    """

    def __init__(self, graph: Optional[ir.CFG] = None, *, apply: bool = True):
        print(f"ctor")
        if graph is not None:
            print("not None")
            self.copy(graph)
            if apply:
                print("apply")
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


class insert_merge_nodes(Transformer):
    """
    Adds block heads when there is a merge

    Makes entry a merge node
    """

    def apply(self):
        nodes = list(self.dfs(self.entry))
        for node in nodes:
            self.single(node)

        # Update entry
        entry = self.add_node(ir.BlockHead(), children=[self.entry])
        self.entry = entry
        return self

    def single(self, node: ir.Element):
        parents = list(self.predecessors(node))
        if len(parents) <= 1:
            return
        for parent in parents:
            self.adj_list[parent] -= {node}
        self.add_node(ir.MergeNode(), *parents, children=[node])

        return self


class add_block_head_after_branch(Transformer):
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
            self.add_node(ir.BlockHead(), node, children=[child])
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
                if node.lvalue == v:
                    worklist.add(node)

        ever_on_worklist |= worklist

        while worklist:
            n = worklist.pop()
            for d in self.dominance_frontier(n):
                if d not in already_has_phi:
                    assert guard(d, ir.BlockHead)

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

    def __init__(self, *args, **kwargs):
        self.visited = set()
        self.var_counter = {}
        self._stacks: dict[expr.Var, list[expr.Var]] = {}
        self.var_mapping = {}
        self.global_vars = set()
        super().__init__(*args, **kwargs)

    def apply(self, recursion: bool = True):
        self.rename(b=self.entry, recursion=recursion)
        assert guard(self.entry, BlockHead)
        print(f"{self.global_vars=}")
        self.entry.phis = {x: {} for x in self.global_vars}
        return self

    def rename(self, b: BlockHead, recursion: bool = True):
        """
        Based on slide 33 of
        https://ics.uci.edu/~yeouln/course/ssa.pdf
        """
        if b in self.visited:
            return
        self.visited.add(b)
        print(f"rename {b=}")

        assert guard(b, BlockHead)
        self.update_phi_lhs(b)

        for stmt in self.subtree_excluding(b, BlockHead):
            self.update_lhs_rhs_stack(stmt)

        for s in self.subtree_leaves(b, BlockHead):
            # For each successor in CFG
            assert guard(s, BlockHead)
            for var, phi in s.phis.items():
                phi[b] = self.stacks(var)[-1]
            print(f"{s=} {b=} {str(s)=} {self._stacks=}")

        # DFS in dominator tree
        if recursion is True:
            for s in self.dominator_tree_iterate():
                if s in self.dominance()[b]:
                    if isinstance(s, ir.BlockHead):
                        self.rename(s)

        # Unwind stack
        for key in b.phis:
            self.stacks(key).pop()
        for stmt in self.subtree_excluding(b, BlockHead):
            if isinstance(stmt, ir.AssignNode):
                self.stacks(stmt.lvalue).pop()

    def stacks(self, var: expr.Var):
        """
        Gets stack for specific var,
        and updates global variables if not seen before
        """
        mapped = self.map_var(var)
        if mapped in self._stacks:
            return self._stacks[mapped]

        new_var = self.gen_name(var)
        self._stacks[var] = [new_var]
        self.global_vars.add(new_var)
        # breakpoint()
        return self.stacks(var)

    def map_var(self, var: expr.Var):
        if var in self.var_mapping:
            return self.var_mapping[var]
        return var

    def update_phi_lhs(self, block: BlockHead):
        replacement = {}
        for v, phis in block.phis.items():
            vn = self.gen_name(v)
            replacement[vn] = phis
        block.phis = replacement

    def update_lhs_rhs_stack(self, stmt: Element):
        if isinstance(stmt, AssignNode):
            for var in get_variables(stmt.rvalue):
                self.stacks(var)
            stmt.rvalue = backwards_replace(
                stmt.rvalue, self.make_mapping(self._stacks)
            )
            stmt.lvalue = self.gen_name(stmt.lvalue)
        if isinstance(stmt, BranchNode):
            for var in get_variables(stmt.cond):
                self.stacks(var)
            stmt.cond = backwards_replace(stmt.cond, self.make_mapping(self._stacks))
        if isinstance(stmt, EndNode):
            new_values = set()
            for var in stmt.values:
                new_values.add(backwards_replace(var, self.make_mapping(self._stacks)))
            stmt.values = new_values

    def gen_name(self, var: expr.Var):
        # Make new unqiue name
        count = self.var_counter.get(var, 0)
        name = f"{var.py_name}.{count}"
        new_var = expr.Var(py_name=name, ver_name=name)
        self.var_counter[var] = count + 1

        # Update var stack
        stack = self._stacks.get(var, [])
        stack.append(new_var)
        self._stacks[var] = stack

        # Update var mapping
        assert new_var not in self.var_mapping
        self.var_mapping[new_var] = var

        return new_var

    def make_mapping(self, mapping_stack: dict[expr.Var, list[expr.Var]]):
        """
        Converts mapping stacks to mapping

        e.g. for an item a -> [x, y, z], the resulting mapping has a -> z
        """
        mapping = {}
        for key, value in mapping_stack.items():
            if value:
                mapping[key] = value[-1]
        return mapping


class parallelize(Transformer):
    """
    Adds parallel paths between two BlockHead nodes
    """

    def apply(self):
        self.single(self.entry, {})
        return super().apply()

    def single(self, block: BlockHead, mapping: dict[expr.Var, expr.Expression]):
        """
        Adds parallel paths between two BlockHead nodes
        """
        for node in self.subtree_excluding(block, BlockHead):
            if isinstance(node, AssignNode):
                node.rvalue = backwards_replace(node.rvalue, mapping)
                mapping[node.lvalue] = node.rvalue
            if isinstance(node, BranchNode):
                node.cond = backwards_replace(node.cond, mapping)

        return self


class dataflow(Transformer):
    """
    Adds data flow edges to graph
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Maps each assignment mode to their SSA variable
        self.mapping = {}
        self.control_entry = Element()  # Temporary

    def apply(self):
        for node in self.adj_list:
            self.make_ssa_mapping(node)

        # for node in self.adj_list:
        #     self.add_cf_to_cf_edges(node)

        # for node in self.adj_list:
        #     self.add_df_to_cf_edges(node)
        # for node in self.adj_list:
        #     self.rm_df_to_cf(node)
        # for node in self.adj_list:
        #     self.add_df_to_cf(node)

        # Cleanup data flow
        for node in list(self.dfs(self.entry)):
            self.add_df_to_df_edges(node)
        # for node in list(self.dfs(self.entry)):
        #     self.rmv_df_to_df_edges(node)

        # for node in list(self.dfs(self.entry)):
        #     self.rmv_cf_to_df_edges(node)
        return self

    def rm_df_to_cf(self, src: Element):
        """
        Removes all data flow to control flow edges whose src is not a FuncNode
        """
        if isinstance(src, (TrueNode, FalseNode, EndNode)):
            for child in set(self.adj_list[src]):
                if isinstance(child, (FuncNode, AssignNode, CallNode)):
                    self.adj_list[src].remove(child)
        if isinstance(src, BranchNode):
            for child in set(self.adj_list[src]):
                if isinstance(child, (AssignNode, EndNode)):
                    self.adj_list[src].remove(child)

    def add_df_to_cf_edges(self, src: Element):
        """
        Adds edge from data flow to its first control flow edge
        """
        # assert len(set(self.subtree_leaves(src, ir.BranchNode))) == 1
        if not isinstance(src, FuncNode):
            return
        for leaf in set(self.subtree_leaves(src, ir.BranchNode)):
            self.adj_list[leaf].add(src)

    def add_df_to_cf(self, node: Element):
        """
        Add data flow edges between data flow nodes
        """
        try:
            if isinstance(node, BranchNode):
                for var in get_variables(node.cond):
                    self.adj_list[self.mapping[var]].add(node)
            if isinstance(node, EndNode):
                for phi in node.phis.values():
                    for var in phi.values():
                        self.adj_list[self.mapping[var]].add(node)

        except Exception as e:
            # print(f"{var=} {self.mapping} {e=}")
            raise e

    def rmv_cf_to_df_edges(self, node: ir.Element):
        """
        Removes control flow to data flow edges
        """
        if isinstance(node, (TrueNode, FalseNode, BranchNode, EndNode)):
            print(f"iter {node=}")
            for child in set(self.adj_list[node]):
                print(f"iter {child=}")
                if isinstance(child, (AssignNode, MergeNode)):
                    self.adj_list[node].remove(child)
                    print(f"Rmv {node=} {child=}")

    def add_cf_to_cf_edges(self, src: Element):
        # Requires to be ran before adding data flow edges
        if isinstance(src, (TrueNode, FalseNode, EndNode)):
            print(f"add_control_flow_edge {src=}")
            for node in list(self.subtree_leaves(src, BranchNode)):
                print(f"adding {node=}")
                self.adj_list[src].add(node)

    def make_ssa_mapping(self, node: Element):
        if isinstance(node, AssignNode):
            self.mapping[node.lvalue] = node
        if isinstance(node, BlockHead):
            for var in node.phis:
                self.mapping[var] = node
        if isinstance(node, FuncNode):
            for var in node.params:
                self.mapping[var] = node

    def add_df_to_df_edges(self, node: Element):
        """
        Add data flow edges between data flow nodes
        """
        try:
            if isinstance(node, AssignNode):
                for var in get_variables(node.rvalue):
                    self.data_flow.add((self.mapping[var], node))
                    # self.adj_list[self.mapping[var]].add(node)
            if isinstance(node, CallNode):
                for var in node.args:
                    self.data_flow.add((self.mapping[var], node))
                    # self.adj_list[self.mapping[var]].add(node)

        except Exception as e:
            # print(f"{var=} {self.mapping} {e=}")
            raise e

    def make_phis_immediate(self, node: Element):
        """
        The element label in PHI nodes replaced with their immediate successor,
        and not their immedate merge node successor
        """
        if not isinstance(node, BlockHead):
            return
        new_phis = {}
        for lhs, phi in node.phis.items():
            new_phis[lhs] = {}
            for rhs in phi.values():
                new_phis[lhs][self.mapping[rhs]] = rhs
        print(f"{repr(node)=}\n{node.phis=}\n{new_phis=}")
        node.phis = new_phis

    def rmv_df_to_df_edges(self, node: Element):
        """
        Remove edges that don't have data flow
        """
        try:
            preds = self.predecessors(node)
            if isinstance(node, AssignNode):
                vars = set(get_variables(node.rvalue))
            elif isinstance(node, CallNode):
                vars = set(node.args)
            else:
                return

            for pred in preds:
                if isinstance(pred, AssignNode):
                    if pred.lvalue not in vars:
                        print(f"remove {repr(pred)} to {repr(node)}")
                        self.adj_list[pred].remove(node)
                elif isinstance(pred, FuncNode):
                    # If all parameters do not include vars
                    for var in pred.params:
                        if var in vars:
                            break
                    else:
                        print(f"remove {repr(pred)} to {repr(node)} {vars=}")
                        self.adj_list[pred].remove(node)
                # elif isinstance(pred, BlockHead):
                #     # If all phi LHSs do not include vars
                #     for var in pred.phis:
                #         if var in vars:
                #             break
                #     else:
                #         print(f"remove {repr(pred)} to {repr(node)} {vars=}")
                #         self.adj_list[pred].remove(node)

        except Exception as e:
            print(f"{var=} {self.mapping} {e=}")
            # raise e


class replace_merge_nodes(Transformer):
    def __init__(self, *args, **kwargs):
        # Mapping of call node to merge node
        self.mapping: dict[ir.Element, ir.Element] = {}

        super().__init__(*args, **kwargs)

    def apply(self):
        for node in self.adj_list.copy():
            self.insert_call(node)
        for node in self.adj_list.copy():
            self.replace_merge_with_func(node)

        # Replace entry with FuncNode
        assert guard(self.entry, ir.BlockHead)
        func_node = FuncNode()
        func_node.params = [key for key in self.entry.phis]
        self.add_node(func_node, children=self.adj_list[self.entry])
        del self[self.entry]
        self.entry = func_node

        return super().apply()

    def insert_call(self, src: ir.Element):
        if not isinstance(src, ir.BlockHead):
            return
        leaves = set(self.subtree_leaves(src, MergeNode))
        subtree = set(self.subtree_excluding(src, BlockHead)) | {src}

        # Pairs of succ(node) -> node, where node is a BlockHead
        pairs: list[tuple[ir.Element, ir.BlockHead]] = []
        print(f"checking {src=} {leaves=} {subtree=}")
        for leaf in leaves:
            for node in subtree:
                if leaf in self.adj_list[node]:
                    pairs.append((node, leaf))
        print(f"{src=} {pairs=}")

        for parent, child in pairs:
            # For each pair, insert a call node
            call_node = CallNode()
            for phi in child.phis.values():
                call_node.args.append(phi[src])

            # Only insert Call if phi merges
            if len(call_node.args) > 0:
                self.add_node(call_node, parent, children=[child])
                self.adj_list[parent].remove(child)

                self.mapping[call_node] = child

        return self

    def replace_merge_with_func(self, src: ir.Element):
        if not isinstance(src, ir.MergeNode):
            return
        preds = self.predecessors(src)

        if len(src.phis) > 0:
            func_node = FuncNode()
            func_node.params = [key for key in src.phis]
            self.add_node(func_node, *preds, children=self.adj_list[src])
            print(f"Deleting {src=}")
            del self[src]
        else:
            for pred in preds:
                self.add_edge(pred, *self.adj_list[src])
            del self[src]


class propagate(Transformer):
    """
    Propagates variables and removes unused/dead variables
    """

    def __init__(self, *args, **kwargs):
        self.mapping: dict[expr.Var, expr.Expression] = {}
        self.used: set[expr.Var] = set()
        self.core: dict[expr.Var, ir.Element] = {}
        self.visited: set[ir.Element] = set()
        self.reference_count: dict[expr.Var, int] = {}
        super().__init__(*args, **kwargs)

    def apply(self):
        for node in self.adj_list:
            self.make_ssa_mapping(node)
        for node in self.adj_list:
            self.make_core_mapping(node)
        print(f"{self.core=}")
        for node in self.adj_list:
            self.dfs_make_mapping(node)
        return self

    def make_reference_count(self, node: Element):
        if isinstance(node, AssignNode):
            for var in get_variables(node.rvalue):
                self.reference_count[var] = self.reference_count.get(var, 0) + 1
        elif isinstance(node, BranchNode):
            for var in get_variables(node.cond):
                self.reference_count[var] = self.reference_count.get(var, 0) + 1
        elif isinstance(node, CallNode):
            for var in node.args:
                self.reference_count[var] = self.reference_count.get(var, 0) + 1

    def make_core_mapping(self, node: Element):
        """
        Variables that are params for function nodes are core variables.
        That is, they cannot be optimized away (except their removal),
        as they're responsible for the PHI functionality
        """
        if isinstance(node, FuncNode):
            for var in node.params:
                self.core[var] = node

    def dfs_make_mapping(self, node: Element):
        """
        Recursively make mapping
        """
        if node in self.visited:
            return
        self.visited.add(node)
        if isinstance(node, AssignNode):
            done = False
            while not done:
                print(f"Iter {node=}")
                vars = list(get_variables(node.rvalue))
                if all(var in self.core for var in vars):
                    done = True
                node.rvalue = backwards_replace(node.rvalue, self.mapping)
        elif isinstance(node, BranchNode):
            done = False
            while not done:
                print(f"Iter {node=}")
                vars = list(get_variables(node.cond))
                if all(var in self.core for var in vars):
                    done = True
                node.cond = backwards_replace(node.cond, self.mapping)
        elif isinstance(node, EndNode):
            done = False
            old_values = node.values
            while not done:
                new_values = []
                for value in old_values:
                    new_values.append(backwards_replace(value, self.mapping))

                variables = []
                for value in new_values:
                    variables.extend(list(get_variables(value)))

                print(f"{new_values=} {variables=} {node.values=} {self.mapping=}")
                if all(var in self.core for var in variables):
                    done = True

                old_values = new_values

            if all(isinstance(value, expr.Var) for value in new_values):
                node.values = new_values

    def make_ssa_mapping(self, node: Element):
        if isinstance(node, AssignNode):
            self.mapping[node.lvalue] = node.rvalue

    def replace(self, src: ir.Element):
        if not isinstance(src, FuncNode):
            return
        for node in set(self.subtree_excluding(src, CallNode)) | set(
            self.subtree_leaves(src, CallNode)
        ):
            if isinstance(node, ir.AssignNode):
                node.rvalue = backwards_replace(node.rvalue, self.mapping)
            elif isinstance(node, ir.BranchNode):
                node.cond = backwards_replace(node.cond, self.mapping)
            # elif isinstance(node, ir.CallNode):
            #     new_args = []
            #     for arg in node.args:
            #         new_args.append(backwards_replace(arg, self.mapping))

    def get_used(self, src: ir.Element):
        if isinstance(src, ir.AssignNode):
            for var in get_variables(src.rvalue):
                self.used.add(var)
        elif isinstance(src, ir.BranchNode):
            for var in get_variables(src.cond):
                self.used.add(var)
        elif isinstance(src, ir.CallNode):
            for var in src.args:
                self.used.add(var)
        elif isinstance(src, ir.EndNode):
            for var in src.values:
                self.used.add(var)

    def rmv_unused_assigns(self, src: ir.Element):
        if not isinstance(src, AssignNode):
            return
        if src.lvalue not in self.used:
            succs = set(self.adj_list[src])
            assert len(succs) == 1
            preds = set(self.predecessors(src))
            for pred in preds:
                self.adj_list[pred] |= succs
            del self[src]

    def rmv_unused_phis(self, src: ir.Element):
        if not isinstance(src, FuncNode):
            return
        for param in src.params.copy():
            print(f"{src=} {param=} {self.used=}")
            if param not in self.used:
                index = src.params.index(param)
                del src.params[index]
                for pred in self.predecessors(src):
                    assert guard(pred, CallNode)
                    del pred.args[index]


class rmv_redundant_calls(Transformer):
    def apply(self):
        for node in self.adj_list.copy():
            self.single(node)
        return self

    def single(self, src: ir.Element):
        if not isinstance(src, FuncNode):
            return
        if len(src.params) == 0:
            func_succs = set(self.adj_list[src])
            assert len(func_succs) == 1
            call_nodes = set(self.predecessors(src))
            for call_node in call_nodes:
                assert guard(call_node, ir.CallNode)
                assert len(call_node.args) == 0
                for call_preds in set(self.predecessors(call_node)):
                    self.adj_list[call_preds] |= func_succs
                del self[call_node]
            del self[src]


class rmv_redundant_branches(Transformer):
    def apply(self):
        for node in self.adj_list.copy():
            self.single(node)
        return self

    def single(self, src: ir.Element):
        if not isinstance(src, BranchNode):
            return

        all_succs = [self.adj_list[x] for x in self.adj_list[src]]
        if all(all_succs[0] == succ for succ in all_succs):
            succs = all_succs[0]
            preds = self.predecessors(src)

            for pred in preds:
                self.adj_list[pred] |= succs

            for branch in self.adj_list[src].copy():
                del self[branch]
            del self[src]


class rmv_assigns_and_phis(Transformer):
    def __init__(self, *args, **kwargs):
        print("subclass ctor")
        self.responsible: dict[expr.Var, ir.Element] = {}
        self.ref_count: dict[expr.Var, int] = {}
        self.to_be_rmved: set[expr.Var] = set()
        super().__init__(*args, **kwargs)

    def apply(self):
        for node in self.adj_list:
            self.make_all_and_used(node)
        print(f"{self.responsible=} {self.ref_count=}")

        self.to_be_rmved = set(self.responsible) - set(
            key for key, value in self.ref_count.items() if value > 0
        )
        print(f"{self.to_be_rmved=}")
        while self.to_be_rmved:
            self.remove(self.to_be_rmved.pop())
            self.to_be_rmved |= set(
                key for key, value in self.ref_count.items() if value == 0
            )
            for var in set(key for key, value in self.ref_count.items() if value == 0):
                del self.ref_count[var]
        print(f"{self.responsible=} {self.ref_count=}")
        return self

    def make_all_and_used(self, src: ir.Element):
        if isinstance(src, AssignNode):
            self.responsible[src.lvalue] = src
            for var in get_variables(src.rvalue):
                self.ref_count[var] = self.ref_count.get(var, 0) + 1
        elif isinstance(src, BranchNode):
            for var in get_variables(src.cond):
                self.ref_count[var] = self.ref_count.get(var, 0) + 1
        elif isinstance(src, CallNode):
            for var in src.args:
                self.ref_count[var] = self.ref_count.get(var, 0) + 1
        elif isinstance(src, FuncNode):
            for var in src.params:
                self.responsible[var] = src
        elif isinstance(src, EndNode):
            for var in src.values:
                self.ref_count[var] = self.ref_count.get(var, 0) + 1

    def remove(self, var: expr.Var):
        print(f"{var=}")
        src = self.responsible[var]
        if src not in self.adj_list:
            return
        if isinstance(src, AssignNode):
            for var in get_variables(src.rvalue):
                self.ref_count[var] -= 1

            succs = set(self.adj_list[src])
            assert len(succs) == 1
            preds = set(self.predecessors(src))
            for pred in preds:
                self.adj_list[pred] |= succs
            del self[src]
        elif isinstance(src, FuncNode):
            index = src.params.index(var)
            del src.params[index]
            for pred in self.predecessors(src):
                assert guard(pred, CallNode)
                self.to_be_rmved.add(pred.args[index])
                del pred.args[index]
