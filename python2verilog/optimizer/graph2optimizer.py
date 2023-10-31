"""
Graph 2 optimizers
"""
import ast
import copy
import itertools
from abc import abstractmethod
import types
from typing import Any, Iterator, Optional

import python2verilog.ir.expressions as expr
import python2verilog.ir.graph2 as ir
from python2verilog.ir.graph2 import *
from python2verilog.ir.graph2 import Optional
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
        print(f"Running {self.__class__.__name__}")
        return self

    @abstractmethod
    def init(self):
        """
        Initialize instance variables
        """
        pass


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
        return super().apply()

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
        return super().apply()


class insert_phis(Transformer):
    """
    Add Phi Nodes
    """

    def apply(self):
        vars = [
            node.lvalue
            for node in self.dfs(self.entry)
            if isinstance(node, ir.AssignNode)
        ]
        for var in vars:
            self.apply_to_var(var)
        return super().apply()

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


class make_ssa(Transformer):
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


class dataflow(Transformer):
    """
    Adds data flow edges to graph
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Maps each assignment mode to their SSA variable
        mapping = {}
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
        return super().apply()

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


class replace_merge_with_call_and_func(Transformer):
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


class propagate_vars_and_consts(Transformer):
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
        return super().apply()

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


class rmv_argless_calls(Transformer):
    def apply(self):
        for node in self.adj_list.copy():
            self.single(node)
        return super().apply()

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
        return super().apply()

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


class rmv_dead_assigns_and_params(Transformer):
    def __init__(self, graph: CFG | None = None, *, apply: bool = True):
        self.var_to_definition: dict[expr.Var, ir.Element] = {}
        self.var_to_ref_count: dict[expr.Var, int] = {}
        self.to_be_removed: set[expr.Var] = set()
        try:
            self.entries = graph.entries
        except:
            pass
        super().__init__(graph, apply=apply)

    def apply(self):
        for node in self.adj_list:
            self.create_ref_count(node)
        print(f"{self.var_to_definition=} {self.var_to_ref_count=}")

        self.to_be_removed = set(self.var_to_definition) - set(
            key for key, value in self.var_to_ref_count.items() if value > 0
        )
        print(f"{self.to_be_removed=}")
        while self.to_be_removed:
            self.remove_unreferenced(self.to_be_removed.pop())
            self.to_be_removed |= set(
                key for key, value in self.var_to_ref_count.items() if value == 0
            )
            for var in set(
                key for key, value in self.var_to_ref_count.items() if value == 0
            ):
                del self.var_to_ref_count[var]
        print(f"{self.var_to_definition=} {self.var_to_ref_count=}")
        return super().apply()

    def create_ref_count(self, src: ir.Element):
        if isinstance(src, AssignNode):
            self.var_to_definition[src.lvalue] = src
            for var in get_variables(src.rvalue):
                self.var_to_ref_count[var] = self.var_to_ref_count.get(var, 0) + 1
        elif isinstance(src, BranchNode):
            for var in get_variables(src.cond):
                self.var_to_ref_count[var] = self.var_to_ref_count.get(var, 0) + 1
        elif isinstance(src, CallNode):
            for var in src.args:
                self.var_to_ref_count[var] = self.var_to_ref_count.get(var, 0) + 1
        elif isinstance(src, FuncNode):
            for var in src.params:
                self.var_to_definition[var] = src
        elif isinstance(src, EndNode):
            for var in src.values:
                self.var_to_ref_count[var] = self.var_to_ref_count.get(var, 0) + 1

    def remove_unreferenced(self, var: expr.Var):
        print(f"{var=}")
        src = self.var_to_definition[var]
        if src not in self.adj_list:
            return
        if isinstance(src, AssignNode):
            for var in get_variables(src.rvalue):
                self.var_to_ref_count[var] -= 1

            succs = set(self.adj_list[src])
            # assert len(succs) == 1
            preds = set(self.predecessors(src))
            for pred in preds:
                self.adj_list[pred] |= succs
            del self[src]
        elif isinstance(src, FuncNode):
            index = src.params.index(var)
            del src.params[index]
            for pred in self.predecessors(src):
                assert guard(pred, CallNode)
                self.to_be_removed.add(pred.args[index])
                del pred.args[index]


class parallelize(Transformer):
    def __init__(self, graph: CFG | None = None, *, apply: bool = True):
        self.stack = []
        super().__init__(graph, apply=apply)

    def apply(self):
        self.stack = list(self.adj_list)
        while self.stack:
            self.single(self.stack.pop())
        # self.single(self[1])
        # self.single(self[2])
        return super().apply()

    def single(self, src: ir.Element):
        if not isinstance(src, ir.AssignNode):
            return
        preds = list(self.predecessors(src))
        if all(
            (self.check(pred, var) for pred in preds)
            for var in get_variables(src.rvalue)
        ):
            succs = self.adj_list[src].copy()
            for pred_pred in self.predecessors(preds[0]):
                self.adj_list[pred_pred].add(src)

            for pred in preds:
                self.adj_list[pred].remove(src)
                self.adj_list[pred] |= succs

    def check(self, src: ir.Element, var: expr.Var):
        if isinstance(src, ir.AssignNode):
            return var != src.lvalue
        if isinstance(src, ir.FuncNode):
            return all(var != v for v in src.params)


class rmv_loops(Transformer):
    def __init__(self, graph: CFG | None = None, *, apply: bool = True):
        self.visited_count: dict[ir.Element, int] = {}
        self.mapping: dict[expr.Var, expr.Expression] = {}
        super().__init__(graph, apply=apply)

    def apply(self):
        self.visited_count = {}
        self.mapping = {}
        self.single(self.entry)
        print(f"{self.mapping=}")
        return super().apply()

    def single(self, src: ir.Element):
        if any(count == 8 for count in self.visited_count.values()):
            return

        if isinstance(src, ir.AssignNode):
            self.mapping[src.lvalue] = src.rvalue
        elif isinstance(src, ir.CallNode):
            for succ in self.adj_list[src]:
                assert guard(succ, ir.FuncNode)
                for arg, param in zip(src.args, succ.params):
                    self.mapping[param] = arg
        for key in self.mapping:
            self.mapping[key] = backwards_replace(self.mapping[key], self.mapping)
        for key in self.mapping:
            try:
                self.mapping[key] = expr.Int(eval(str(self.mapping[key])))
            except Exception as e:
                print(f"{e=} {str(self.mapping[key])=}")

        self.visited_count[src] = self.visited_count.get(src, 0) + 1
        for succ in self.adj_list[src]:
            self.single(succ)


class lower_to_fsm(Transformer):
    def __init__(self, graph: CFG | None = None, *, apply: bool = True):
        self.new: ir.CFG = ir.CFG()
        self.new.unique_counter = 100
        self.visited_count: dict[ir.Element, int] = {}
        self.mapping: dict[expr.Var, expr.Expression] = {}
        self.truely_visited: set[ir.Element] = set()
        self.entries = set()
        super().__init__(graph, apply=apply)

    def apply(self):
        self.clone(self.entry)
        # self.clone(self[12])
        self.copy(self.new)
        return super().apply()

    def clone(self, src: ir.Element):
        new_node = copy.copy(src)
        new_node.graph = None
        new_node._unique_id = ""

        # print(f"{new_node=} {str(new_node)=} {self.mapping=}")
        print(f"{self.visited_count=} {self.mapping=}")
        if isinstance(new_node, ir.AssignNode):
            new_node.rvalue = backwards_replace(new_node.rvalue, self.mapping)
        elif isinstance(new_node, BranchNode):
            new_node.cond = backwards_replace(new_node.cond, self.mapping)
        elif isinstance(new_node, EndNode):
            new_values = []
            for value in new_node.values:
                new_values.append(backwards_replace(value, self.mapping))
            new_node.values = new_values

        self.new.add_node(new_node)
        if len(self.visited_count) == 0:
            self.entries.add(new_node)

        self.visited_count[src] = self.visited_count.get(src, 0) + 1
        if self.visited_count[src] > 3 and isinstance(src, FuncNode):
            print(f"DONE {src=}")

            if src not in self.truely_visited:
                print(f"RECURSE {src=} {self.mapping=}")

                self.visited_count = {}
                self.mapping = {}
                self.truely_visited.add(src)
                self.clone(src)

            return new_node

        if isinstance(src, ir.FuncNode):
            for param in src.params:
                self.mapping[param] = param
        elif isinstance(src, ir.AssignNode):
            if src.lvalue in self.mapping:
                # raise RuntimeError(f"{src.lvalue=}")
                pass
            else:
                self.mapping[src.lvalue] = src.rvalue
        elif isinstance(src, ir.CallNode):
            # print(f"Inner")
            for succ in self.adj_list[src]:
                assert guard(succ, ir.FuncNode)
                for arg, param in zip(src.args, succ.params):
                    self.mapping[param] = arg

        for node in self.adj_list[src]:
            # print(f"{self.mapping=}")

            # for key in self.mapping:
            #     if self.mapping[key] in get_variables(self.mapping[key]):
            #         # temp fix to prevent infinite recursion
            #         continue
            #     self.mapping[key] = backwards_replace(self.mapping[key], self.mapping)

            print(f"Add node {src=} -> {new_node=}")
            new_child = self.clone(node)
            print(f"Add edge {new_node=} -> {new_child=}")

            self.new.add_edge(new_node, new_child)
        return new_node


class make_nonblocking(Transformer):
    def __init__(self, graph: CFG | None = None, *, apply: bool = True):
        self.counter = 0
        self.entries = graph.entries
        super().__init__(graph, apply=apply)

    def apply(self):
        print(f"{self.entries}")
        for entry in self.entries:
            self.start(entry)
        return super().apply()

    def start(
        self,
        src: ir.Element,
        indent: int = 0,
        mapping: Optional[dict[expr.Var, expr.Expression]] = None,
    ):
        if mapping is None:
            mapping = {}
        if isinstance(src, ir.FuncNode):
            yield "  " * indent + f"def func({str(src.params)[1:-1]}):"
            if len(list(self.adj_list[src])) == 1:
                yield from self.start(list(self.adj_list[src])[0], indent + 1, mapping)
        elif isinstance(src, ir.AssignNode):
            self.counter += 1
            if self.counter > 1000:
                return
            print(f"{src} {mapping=}")
            src.rvalue = backwards_replace(src.rvalue, mapping)
            mapping[src.lvalue] = src.rvalue
            yield "  " * indent + f"{src.lvalue} = {src.rvalue}"
            yield from self.start(list(self.adj_list[src])[0], indent, mapping)
        elif isinstance(src, ir.CallNode):
            new_args = []
            for arg in src.args:
                new_args.append(backwards_replace(arg, mapping))
            src.args = new_args

            func = list(self.adj_list[src])[0]
            assert guard(func, ir.FuncNode)

            assign_nodes = []
            for arg, param in zip(src.args, func.params):
                mapping[param] = arg
                yield "  " * indent + f"{param} = {arg}"
                assign_nodes.append(AssignNode(param, arg))

            succ = list(self.predecessors(src))[0]
            for assign in assign_nodes:
                succ = self.add_node(assign, succ)

            if len(list(self.adj_list[func])) == 1:
                self.add_edge(assign_nodes[-1], list(self.adj_list[func])[0])
                yield from self.start(list(self.adj_list[func])[0], indent, mapping)
                del self[src]
                del self[func]

        elif isinstance(src, ir.BranchNode):
            src.cond = backwards_replace(src.cond, mapping)

            yield "  " * indent + f"if {src.cond}:"
            true, false = list(self.adj_list[src])
            if isinstance(false, ir.TrueNode):
                false, true = true, false
            yield from self.start(
                list(self.adj_list[true])[0], indent + 1, copy.deepcopy(mapping)
            )
            yield "  " * indent + "else:"
            yield from self.start(
                list(self.adj_list[false])[0], indent + 1, copy.deepcopy(mapping)
            )
        elif isinstance(src, ir.EndNode):
            new_values = []
            for value in src.values:
                new_values.append(backwards_replace(value, mapping))
            src.values = new_values
            yield "  " * indent + f"return {src.values}"


class codegen(Transformer):
    def __init__(self, graph: CFG | None = None, *, apply: bool = True):
        self.counter = 0
        self.entries = graph.entries
        super().__init__(graph, apply=apply)

    def apply(self):
        for entry in self.entries:
            self.start(entry)
        return super().apply()

    def start(
        self,
        src: ir.Element,
        indent: int = 0,
        mapping: Optional[dict[expr.Var, expr.Expression]] = None,
    ):
        if mapping is None:
            mapping = {}
        if isinstance(src, ir.FuncNode):
            yield "  " * indent + f"def func({str(src.params)[1:-1]}):"
            if len(list(self.adj_list[src])) == 1:
                yield from self.start(list(self.adj_list[src])[0], indent + 1, mapping)
        elif isinstance(src, ir.AssignNode):
            self.counter += 1
            if self.counter > 1000:
                return
            print(f"{src} {mapping=}")
            src.rvalue = backwards_replace(src.rvalue, mapping)
            mapping[src.lvalue] = src.rvalue
            yield "  " * indent + f"{src.lvalue} = {src.rvalue}"
            yield from self.start(list(self.adj_list[src])[0], indent, mapping)
        elif isinstance(src, ir.CallNode):
            new_args = []
            for arg in src.args:
                new_args.append(backwards_replace(arg, mapping))
            src.args = new_args

            func = list(self.adj_list[src])[0]
            assert guard(func, ir.FuncNode)

            # assign_nodes = []
            for arg, param in zip(src.args, func.params):
                mapping[param] = arg
                # yield "  " * indent + f"{param} = {arg}"
                # assign_nodes.append(AssignNode(param, arg))

            if len(list(self.adj_list[func])) == 1:
                yield from self.start(list(self.adj_list[func])[0], indent, mapping)

        elif isinstance(src, ir.BranchNode):
            src.cond = backwards_replace(src.cond, mapping)

            yield "  " * indent + f"if {src.cond}:"
            true, false = list(self.adj_list[src])
            if isinstance(false, ir.TrueNode):
                false, true = true, false
            yield from self.start(
                list(self.adj_list[true])[0], indent + 1, copy.deepcopy(mapping)
            )
            yield "  " * indent + "else:"
            yield from self.start(
                list(self.adj_list[false])[0], indent + 1, copy.deepcopy(mapping)
            )
        elif isinstance(src, ir.EndNode):
            new_values = []
            for value in src.values:
                new_values.append(backwards_replace(value, mapping))
            src.values = new_values
            yield "  " * indent + f"return {src.values}"
