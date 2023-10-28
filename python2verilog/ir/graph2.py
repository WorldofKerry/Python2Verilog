"""
Graph v2
"""

from __future__ import annotations

import copy
import logging
import reprlib
from typing import Collection, Iterator, Optional, Union

from python2verilog.ir import expressions as expr
from python2verilog.utils.lines import Lines
from python2verilog.utils.typed import guard, typed, typed_list, typed_set, typed_strict


class Element:
    """
    Element, base class for vertex or edge
    """

    def __init__(self, unique_id: str = ""):
        self._unique_id = typed_strict(unique_id, str)
        self.graph: Optional[CFG] = None

    def __hash__(self) -> int:
        assert len(self.unique_id) > 0, f'"{self.unique_id}"'
        return hash(self.unique_id)

    def __eq__(self, value: object):
        if isinstance(value, Element):
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

    @reprlib.recursive_repr()
    def __str__(self) -> str:
        return f"%{self.unique_id}: "

    def __repr__(self) -> str:
        return f"{self.unique_id}"


class BasicBlock(Element):
    def __init__(self, operations: Optional[list[Element]] = None, unique_id: str = ""):
        super().__init__(unique_id)
        self.statements = [] if operations is None else operations

    def __str__(self) -> str:
        lines = Lines(f"{super().__str__()}BasicBlock\n")
        for operation in self.statements:
            lines += f"{operation}"
        return lines.to_string()


class BlockHead(Element):
    """
    Similar to MLIR block arguments
    """

    def __init__(self, unique_id: str = ""):
        super().__init__(unique_id)
        self.phis: dict[expr.Var, dict[Element, expr.Var]] = {}

    def stringify_phis(self):
        lines = Lines()
        for key, inner in self.phis.items():
            lines += f"{key} = \u03d5 " + ", ".join(
                map(lambda x: f"[{x[1]}, %{x[0].unique_id}]", inner.items())
            )
        return str(lines)


class AssignNode(Element):
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


class ClockNode(Element):
    """
    A clock edge occurs, includes phi of variables
    """

    def __str__(self) -> str:
        return super().__str__() + "Clock"


class BranchNode(Element):
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


class EndNode(BlockHead):
    """
    A node indicate the end of a frame,
    whether it be a function return or a coroutine yield
    """

    def __init__(self, values: set[expr.Var], unique_id: str = ""):
        super().__init__(unique_id)
        self.phis = {value: {} for value in values}
        self.values = typed_set(values, expr.Var)

    def __str__(self) -> str:
        return (
            super().__str__()
            + f"{EndNode.__name__[:-4]}\n"
            + self.stringify_phis()
            + f"{self.values}"
        )


class CallNode(Element):
    def __init__(self, unique_id: str = ""):
        super().__init__(unique_id)
        self.args: list[expr.Var] = []

    def __str__(self) -> str:
        return super().__str__() + f"{self.__class__.__name__[:-4]}" + f"\n{self.args}"


class FuncNode(Element):
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

    DUMMY = Element("___DUMMY___")

    def __init__(self, prefix: str = ""):
        self.adj_list: dict[Element, set[Element]] = {}
        self.unique_counter = -1
        self.prefix = typed_strict(prefix, str)
        self.entry = CFG.DUMMY

    def move(self, graph: CFG):
        """
        Move constructor
        """
        self.adj_list = graph.adj_list
        self.unique_counter = graph.unique_counter
        self.prefix = graph.prefix
        self.entry = graph.entry
        return self

    def copy(self, graph: CFG):
        """
        Copy constructor that assumes graph elements are immutable
        """
        self.adj_list = {}
        for key, value in graph.adj_list.items():
            self.adj_list[key] = copy.copy(value)
        self.unique_counter = graph.unique_counter
        self.prefix = graph.prefix
        self.entry = graph.entry
        return self

    def add_node(
        self,
        element: Element,
        *parents: Collection[Element],
        children: Optional[Collection[Element]] = None,
    ) -> Element:
        """
        Add node with new unique_id

        Gives node a unique id if it doesn't have one
        """
        assert guard(element, Element)

        if element.graph:
            raise RuntimeError(
                f"Element is already apart of a graph {element} {element.graph}"
            )
        element.graph = self

        if not element.unique_id:
            element.set_unique_id(self._next_unique())

        if element in self.adj_list:
            raise RuntimeError(
                "Element already exists" f" {self.adj_list[element]} {element}"
            )

        for parent in parents:
            assert guard(parent, Element)
            self.adj_list[parent].add(element)
        self.adj_list[element] = set(children) if children else set()

        if self.entry is CFG.DUMMY:
            self.entry = element

        return element

    def validate(self):
        """
        Validate graph instance
        """
        assert guard(self.adj_list, dict)
        for elem, children in self.adj_list.items():
            assert guard(elem, Element)
            assert guard(children, set), f"{children} {type(children)}"
            for child in children:
                assert guard(child, Element)
                assert child in self.adj_list
        assert guard(self.prefix, str)
        assert guard(self.unique_counter, int)

    def add_edge(self, source: Element, *targets: Element):
        """
        Add directed edge
        """
        assert all(target not in self.adj_list[source] for target in targets)
        self.adj_list[source] = self.adj_list[source].union(targets)

    def __getitem__(self, key: Union[Element, str, int]):
        if isinstance(key, Element):
            return self.adj_list[key]
        if isinstance(key, (str, int)):
            key = str(key)
            for elem in self.adj_list:
                if elem.unique_id == key:
                    return elem
        raise TypeError(f"{key} {type(key)}")

    def __delitem__(self, key: Union[Element, str]):
        if isinstance(key, Element):
            del self.adj_list[key]
            for children in self.adj_list.values():
                if key in children:
                    children.remove(key)
            return
        if self.entry == key:
            self.entry = None
        raise TypeError()

    def predecessors(self, element: Element) -> Iterator[Element]:
        """
        Get immediate successors/parents of a element
        """
        for parent, children in self.adj_list.items():
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
        for elem, children in self.adj_list.items():
            lines += f"{repr(elem)}: {str(children)[1:-1] if children else 'none'}"
        return str(lines)

    def to_cytoscape(
        self, use_repr: bool = False
    ) -> dict[str, list[dict[str, dict[str, str]]]]:
        """
        To cytoscape visualizer
        """
        nodes = []
        edges = []

        for elem, children in self.adj_list.items():
            nodes.append(
                {
                    "data": {
                        "id": elem.unique_id,
                        "label": repr(elem) if use_repr else str(elem),
                    }
                }
            )
            for child in children:
                control_flow_t = TrueNode, FalseNode, BranchNode, EndNode
                data_flow_t = AssignNode, MergeNode, FuncNode, CallNode
                if isinstance(elem, control_flow_t) and isinstance(
                    child, control_flow_t
                ):
                    classs = "ControlFlow"
                elif isinstance(elem, data_flow_t) and isinstance(child, data_flow_t):
                    classs = "DataFlow"
                else:
                    classs = "Mapper"
                edges.append(
                    {
                        "data": {
                            "source": elem.unique_id,
                            "target": child.unique_id,
                            "class": classs,
                            "label": classs,
                        }
                    }
                )

        return {"nodes": nodes, "edges": edges}

    def dfs(
        graph: CFG, source: Element, visited: Optional[set[Element]] = None
    ) -> Iterator[Element]:
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
            yield from graph.dfs(child, visited)

    def dominance(graph: CFG) -> dict[Element, set[Element]]:
        """
        Returns dict dominance relations,

        i.e. k in ret[n] means n dominates k
        """
        vertices = set(graph.dfs(graph.entry))
        dominance_ = {}

        for vertex in vertices:
            temp_graph = CFG().copy(graph)
            del temp_graph[vertex]
            new_vertices = set(temp_graph.dfs(graph.entry))
            delta = vertices - new_vertices
            dominance_[vertex] = delta
        # logging.debug(f"\n{print_tree(dominance_, graph.entry)}")
        return dominance_

    def dominance_frontier(graph: CFG, n: Element):
        """
        Gets dominator frontier of n with respect to graph entry

        DF(N) = {Z | M→Z & (N dom M) & ¬(N sdom Z)}

        for Z, M, N in set of Nodes
        """
        dominance_ = graph.dominance()

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
                        f"{graph.dominance_frontier.__name__} {z=} {m=} {m_to_z=} {n_dom_m=} {n_sdom_z=}"
                    )

    def dominator_tree(self: CFG):
        """
        Returns dict representing dominator tree
        """
        visited = set()
        nodes = reversed(list(self.dfs(self.entry)))
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
        queue = [self.entry]
        while queue:
            cur = queue.pop(0)
            yield cur
            for child in dom_tree.get(cur, set()):
                if child != cur:
                    queue.append(child)

    def subtree_excluding(self, source: Element, elem_type: type[Element]):
        """
        Builds a subtree rooted at source,
        where every leaf is type elem_type,
        and all paths from source to leaves contain x node(s) of type elem_type,
        where x is 2 if type of source is elem_type else 1

        Yields all nodes in subtree, excluding leaves
        """
        for child in self.adj_list[source]:
            if not isinstance(child, elem_type):
                yield child
                yield from self.subtree_excluding(child, elem_type)

    def subtree_leaves(
        self,
        source: Element,
        elem_type: type[Element],
        visited: Optional[set[Element]] = None,
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
        for child in self.adj_list[source]:
            if isinstance(child, elem_type):
                yield child
            else:
                yield from self.subtree_leaves(child, elem_type, visited)
