"""
Graph v2
"""

from __future__ import annotations

import copy
import logging
import reprlib
from typing import Collection, Iterator, Optional, Sequence, Union

from python2verilog.ir import expressions as expr
from python2verilog.utils.lines import Lines
from python2verilog.utils.typed import guard, typed, typed_list, typed_set, typed_strict


class Node2:
    """
    Element, base class for vertex or edge
    """

    def __init__(self, unique_id: str = ""):
        self._unique_id = typed_strict(unique_id, str)

    def __hash__(self) -> int:
        assert len(self.unique_id) > 0, f'"{self.unique_id}"'
        return hash(self.unique_id)

    def __eq__(self, value: object):
        if isinstance(value, Node2):
            return self.unique_id == value.unique_id
        return False

    @property
    def unique_id(self):
        """
        Unique id
        """
        return self._unique_id

    def set_unique_id(self, unique_id: str):
        """
        Sets unique id
        """
        assert len(self._unique_id) == 0
        self._unique_id = typed_strict(unique_id, str)

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))
        result._unique_id = self._unique_id
        return result

    @reprlib.recursive_repr()
    def __str__(self) -> str:
        return f"%{self.unique_id}: "

    def __repr__(self) -> str:
        return f"{self.unique_id}"


class BasicBlock(Node2):
    def __init__(self, operations: Optional[list[Node2]] = None, unique_id: str = ""):
        super().__init__(unique_id)
        self.statements = [] if operations is None else operations

    def __str__(self) -> str:
        lines = Lines(f"{super().__str__()}BasicBlock\n")
        for operation in self.statements:
            lines += f"{operation}"
        return lines.to_string()


class BlockHead(Node2):
    """
    Similar to MLIR block arguments
    """

    def __init__(self, unique_id: str = ""):
        super().__init__(unique_id)
        self.phis: dict[expr.Var, dict[Node2, expr.Var]] = {}

    def stringify_phis(self):
        lines = Lines()
        for key, inner in self.phis.items():
            lines += f"{key} = \u03d5 " + ", ".join(
                map(lambda x: f"[{x[1]}, %{x[0].unique_id}]", inner.items())
            )
        return str(lines)


class AssignNode(Node2):
    """
    Variable assignment
    """

    def __init__(
        self,
        lvalue: expr.Var,
        rvalue: expr.Expression,
        unique_id: str = "",
        **kwargs,
    ):
        super().__init__(unique_id, **kwargs)
        self.lvalue = typed_strict(lvalue, expr.Var)
        self.rvalue = typed_strict(rvalue, expr.Expression)

    def __str__(self) -> str:
        return super().__str__() + f"{self.lvalue} = {self.rvalue}"


class ClockNode(Node2):
    """
    A clock edge occurs, includes phi of variables
    """

    def __str__(self) -> str:
        return super().__str__() + "Clock"


class BranchNode(Node2):
    """
    Conditional branch
    """

    def __init__(self, expression: expr.Expression, unique_id: str = ""):
        super().__init__(unique_id)
        self.cond = typed_strict(expression, expr.Expression)

    def __str__(self) -> str:
        return super().__str__() + f"If {self.cond}"


class MergeNode(BlockHead):
    """
    Merge node
    """

    def __str__(self) -> str:
        return (
            super().__str__() + f"{MergeNode.__name__[:-4]}\n" + self.stringify_phis()
        )


class TrueNode(BlockHead):
    """
    A true node for branch
    """

    def __str__(self) -> str:
        return super().__str__() + f"{TrueNode.__name__[:-4]}\n" + self.stringify_phis()


class FalseNode(BlockHead):
    """
    A false node for branch
    """

    def __str__(self) -> str:
        return (
            super().__str__() + f"{FalseNode.__name__[:-4]}\n" + self.stringify_phis()
        )


class EndNode(Node2):
    """
    A node indicate the end of a frame,
    whether it be a function return or a coroutine yield
    """

    def __init__(self, values: list[expr.Expression], unique_id: str = ""):
        super().__init__(unique_id)
        self.values: list[expr.Expression] = typed_list(values, expr.Expression)

    def __str__(self) -> str:
        return super().__str__() + f"{EndNode.__name__[:-4]}\n" + f"{self.values}"


class CallNode(Node2):
    def __init__(self, unique_id: str = ""):
        super().__init__(unique_id)
        self.args: list[expr.Var] = []

    def __str__(self) -> str:
        return super().__str__() + f"{self.__class__.__name__[:-4]}" + f"\n{self.args}"


class FuncNode(Node2):
    def __init__(self, unique_id: str = ""):
        super().__init__(unique_id)
        self.params: list[expr.Var] = []

    def __str__(self) -> str:
        return (
            super().__str__() + f"{self.__class__.__name__[:-4]}" + f"\n{self.params}"
        )


class CFG:
    """
    Graph
    """

    DUMMY = Node2("___DUMMY___")

    def __init__(self, prefix: str = ""):
        self._adj_list: dict[Node2, set[Node2]] = {}

        # Unused
        self.prefix = typed_strict(prefix, str)

        # Incremented before usage (i.e. current value is already used)
        self.unique_counter = -1

        # The initial entry is stored as None -> Element
        self.exit_to_entry: dict[Optional[CallNode], FuncNode] = {}

    def copy(self, graph: CFG):
        """
        Copy constructor that assumes graph elements are immutable
        """

        # Regular values
        self.unique_counter = graph.unique_counter
        self.prefix = graph.prefix

        self._adj_list = copy.deepcopy(graph._adj_list)

        # Make sure exit to entry uses same elements as new copy used in of adj_list
        self.exit_to_entry = {}
        for exit, entry in graph.exit_to_entry.items():
            if exit is None:
                self.exit_to_entry[None] = self.id_to_node(entry.unique_id)
            else:
                self.exit_to_entry[self.id_to_node(exit.unique_id)] = self.id_to_node(
                    entry.unique_id
                )

        return self

    def id_to_node(self, id: object):
        id = str(id)
        for key in self._adj_list:
            if key.unique_id == id:
                return key
        raise RuntimeError()

    def successors(self, node: Node2) -> set[Node2]:
        return set(self._adj_list[node])

    def nodes(self):
        return list(self._adj_list.keys())

    def add_node(
        self,
        node: Node2,
        *parents: Collection[Node2],
        children: Optional[Collection[Node2]] = None,
    ) -> Node2:
        """
        Add node with new unique_id

        Gives node a unique id if it doesn't have one
        """
        assert guard(node, Node2)

        if not node.unique_id:
            node.set_unique_id(self._next_unique())

        if node in self.nodes():
            raise RuntimeError(
                "Element already exists" f" {self._adj_list[node]} {node}"
            )

        self._adj_list[node] = set()
        for parent in parents:
            self.add_edge(parent, node, strict=True)
        if children:
            self.add_edge(node, *children, strict=True)

        self.exit_to_entry[None] = self.exit_to_entry.get(None, node)

        return node

    def validate(self):
        """
        Validate graph instance
        """
        assert guard(self._adj_list, dict)
        for elem, children in self._adj_list.items():
            assert guard(elem, Node2)
            assert guard(children, set), f"{children} {type(children)}"
            for child in children:
                assert guard(child, Node2)
                assert child in self._adj_list
        assert guard(self.prefix, str)
        assert guard(self.unique_counter, int)

    def add_edge(self, source: Node2, *targets: Node2, strict: bool = False):
        """
        Add directed edge
        """
        assert guard(source, Node2)
        assert all(guard(target, Node2) for target in targets)

        if strict:
            # Check that edge doesn't already exist
            assert all(target not in self._adj_list[source] for target in targets)

        self._adj_list[source] = self._adj_list[source].union(targets)

    def remove_edge(self, source: Node2, target: Node2):
        assert guard(source, Node2)
        assert guard(target, Node2)
        self._adj_list[source].remove(target)

    def remove_node(self, key: Node2):
        del self._adj_list[key]
        for children in self._adj_list.values():
            if key in children:
                children.remove(key)
        for k, v in list(self.exit_to_entry.items()):
            if k == key:
                del self.exit_to_entry[k]
            if v == key:
                del self.exit_to_entry[k]

    def __delitem__(self, key: Union[Node2, str]):
        if isinstance(key, Node2):
            self.remove_node(key)
            return
        raise TypeError()

    def predecessors(self, element: Node2) -> Iterator[Node2]:
        """
        Get immediate successors/parents of a element
        """
        for parent, children in self._adj_list.items():
            if element in children:
                yield parent

    def _next_unique(self):
        """
        Get next unique name
        """
        self.unique_counter += 1
        return f"{self.prefix}{self.unique_counter}"

    def __str__(self) -> str:
        lines = Lines(f"Graph with prefix `{self.prefix}`")
        # for elem, children in self.adj_list.items():
        #     lines += f"{repr(elem)}: {str(children)[1:-1] if children else 'none'}"
        return str(lines)

    def to_cytoscape(
        self, use_repr: bool = False, id_prefix: str = ""
    ) -> dict[str, list[dict[str, dict[str, str]]]]:
        """
        To cytoscape visualizer
        """
        nodes = []
        edges = []

        for elem, children in self._adj_list.items():
            nodes.append(
                {
                    "data": {
                        "id": f"{id_prefix}{elem.unique_id}",
                        "label": repr(elem) if use_repr else str(elem),
                    }
                }
            )
            for child in children:
                # control_flow_t = TrueNode, FalseNode, BranchNode, EndNode
                # data_flow_t = AssignNode, MergeNode, FuncNode, CallNode
                # if isinstance(elem, control_flow_t) and isinstance(
                #     child, control_flow_t
                # ):
                #     classs = "ControlFlow"
                # elif isinstance(elem, data_flow_t):
                #     classs = "DataFlow"
                # elif isinstance(elem, control_flow_t) and isinstance(
                #     child, data_flow_t
                # ):
                #     classs = "Mapper"
                edges.append(
                    {
                        "data": {
                            "source": f"{id_prefix}{elem.unique_id}",
                            "target": f"{id_prefix}{child.unique_id}",
                            "class": "ControlFlow",
                            "label": "",
                        }
                    }
                )
        for k, v in self.exit_to_entry.items():
            if k is not None:
                edges.append(
                    {
                        "data": {
                            "source": f"{id_prefix}{k.unique_id}",
                            "target": f"{id_prefix}{v.unique_id}",
                            "class": "Mapper",
                            "label": "",
                        }
                    }
                )

        return {"nodes": nodes, "edges": edges}

    def dfs(
        graph: CFG, source: Node2, visited: Optional[set[Node2]] = None
    ) -> Iterator[Node2]:
        """
        Depth-first search
        """
        if visited is None:
            visited = set()
        if source in visited:
            return
        if source not in graph._adj_list:
            return
        visited.add(source)
        yield source
        for child in graph.successors(source):
            yield from graph.dfs(child, visited)

    def dominance(graph: CFG) -> dict[Node2, set[Node2]]:
        """
        Returns dict dominance relations,

        i.e. k in ret[n] means n dominates k
        """
        vertices = set(graph.dfs(graph.exit_to_entry[None]))
        dominance_ = {}

        for vertex in vertices:
            temp_graph = CFG().copy(graph)
            del temp_graph[vertex]
            new_vertices = set(temp_graph.dfs(graph.exit_to_entry[None]))
            delta = vertices - new_vertices
            dominance_[vertex] = delta
        # logging.debug(f"\n{print_tree(dominance_, graph.entry)}")
        return dominance_

    def dominance_frontier(graph: CFG, n: Node2):
        """
        Gets dominator frontier of n with respect to graph entry

        DF(N) = {Z | M→Z & (N dom M) & ¬(N sdom Z)}

        for Z, M, N in set of Nodes
        """
        dominance_ = graph.dominance()

        zs = graph._adj_list.keys()
        ms = graph._adj_list.keys()

        for z in zs:
            for m in ms:
                # M -> Z
                m_to_z = z in graph._adj_list[m]

                # N dom M
                n_dom_m = m in dominance_[n]

                # ~(N sdom Z)
                n_sdom_z = z in dominance_[n] and n != z

                if m_to_z and n_dom_m and not n_sdom_z:
                    yield z
                else:
                    logging.debug(
                        f"{graph.dominance_frontier.__name__} {z=} {m=} {m_to_z=} {n_dom_m=} {n_sdom_z=}"
                    )

    def dominator_tree(self: CFG):
        """
        Returns dict representing dominator tree
        """
        visited = set()
        nodes = reversed(list(self.dfs(self.exit_to_entry[None])))
        dom_tree = {}
        dominance_ = self.dominance()
        for node in nodes:
            temp = dominance_[node] - visited - {node}
            if len(temp) > 0:
                dom_tree[node] = temp
            visited |= temp

        # return {key.unique_id: set(map(lambda x: x.unique_id, value)) for key, value in dom_tree.items()}
        return dom_tree

    def dominator_tree_iterate(self: CFG):
        """
        Yields nodes of dominator tree
        """
        # dom_tree = self.dominator_tree()
        # print(f"{dom_tree=}")

        # def rec(node: Element):
        #     print(f"{node=}")
        #     for child in dom_tree.get(node, set()):
        #         if node != child:
        #             yield from rec(child)

        # yield from rec(self.entry)

        dom_tree = self.dominator_tree()
        # print(f"{dom_tree=}")
        queue = [self.exit_to_entry[None]]
        while queue:
            cur = queue.pop(0)
            yield cur
            for child in dom_tree.get(cur, set()):
                if child != cur:
                    queue.append(child)

    def subtree_excluding(self, source: Node2, elem_type: type[Node2]):
        """
        Builds a subtree rooted at source,
        where every leaf is type elem_type,
        and all paths from source to leaves contain x node(s) of type elem_type,
        where x is 2 if type of source is elem_type else 1

        Yields all nodes in subtree, excluding leaves
        """
        stack = list(self._adj_list[source])
        while stack:
            cur = stack.pop()
            if isinstance(cur, elem_type):
                continue
            yield cur
            for child in self._adj_list[cur]:
                stack.append(child)

    def subtree_leaves(
        self,
        source: Node2,
        elem_type: type[Node2],
        visited: Optional[set[Node2]] = None,
    ):
        """
        Builds a subtree rooted at source,
        where every leaf is type elem_type,
        and all paths from source to leaves contain x node(s) of type elem_type,
        where x is 2 if type of source is elem_type else 1

        Yields all leaves in subtree
        """
        if visited is None:
            visited = set()
        if source in visited:
            return
        visited.add(source)
        for child in self._adj_list[source]:
            if isinstance(child, elem_type):
                yield child
            else:
                yield from self.subtree_leaves(child, elem_type, visited)
