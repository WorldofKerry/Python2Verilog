"""
Graph v2
"""

from __future__ import annotations
import copy
import logging

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

    def __repr__(self) -> str:
        return f"{self.unique_id}[{self}]"


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
        return f"{self.lvalue} = {self.rvalue}"


class ClockNode(Element):
    """
    A clock edge occurs
    """

    def __str__(self) -> str:
        return "Clock"


class BranchNode(Element):
    """
    Conditional branch
    """

    def __init__(self, expression: expr.Expression, unique_id: str = ""):
        super().__init__(unique_id)
        self.expression = typed_strict(expression, expr.Expression)

    def __str__(self) -> str:
        return f"if {self.expression}"


class TrueNode(Element):
    """
    A true node for branch
    """

    def __str__(self) -> str:
        return "True"


class FalseNode(Element):
    """
    A false node for branch
    """

    def __str__(self) -> str:
        return "False"


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

    def mimic(self, graph: CFG):
        """
        In-place copy
        """
        self.adj_list = graph.adj_list
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

    def __getitem__(self, key: Union[Element, str]):
        if isinstance(key, Element):
            return self.adj_list[key]
        if isinstance(key, str):
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
        raise TypeError()

    def immediate_successors(self, element: Element) -> Iterator[Element]:
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
        self, id_in_label: bool = False
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
                        "label": repr(elem) if id_in_label else str(elem),
                    }
                }
            )
            for child in children:
                edges.append(
                    {
                        "data": {
                            "source": elem.unique_id,
                            "target": child.unique_id,
                        }
                    }
                )

        return {"nodes": nodes, "edges": edges}
